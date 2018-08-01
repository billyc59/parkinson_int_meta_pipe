#!/usr/bin/env python

import sys
import os
import os.path
from argparse import ArgumentParser
from configparser import ConfigParser
import multiprocessing as mp
import MetaPro_commands as mpcom
import MetaPro_paths as mpp
import time


def make_folder(folder_path):
    if not (os.path.exists(folder_path)):
        os.makedirs(folder_path)


# Used to determine quality encoding of fastq sequences.
# Assumes Phred+64 unless there is a character within the first 10000 reads with encoding in the Phred+33 range.
def determine_encoding(fastq):
    encoding = 64
    with open(fastq) as fq:
        line_count = 0
        encoding_count = 0
        for line in fq:
            line_count += 1
            if line_count % 4 == 0:
                encoding_count += 1
                for char in line:
                    if ord(char) < 64: #logic is: if the ascii code falls under 64, then it's Phred+33
                        encoding = 33
                        break
                if encoding_count == 10000 or encoding == 33:
                    break

    return encoding


# handles where to kill the pipeline, due to the prev step behaving badly
#logic is:  if the files inside the dep_path (or dep job label shortcut to the final_results)
#           are empty, then there's an error.  kill the pipeline 
def check_where_kill(dep_job_label=None, dep_path=None):
    if dep_job_label is None:
        if dep_path is None:
            return True
        else:
            dep_job_path = dep_path
    else:
        dep_job_path = os.path.join(dep_job_label, "data", "final_results")

    file_list = os.listdir(dep_job_path)
    if len(file_list) > 0:
        for item in file_list:
            file_check_path = os.path.join(dep_job_path, item)
            if (os.path.getsize(file_check_path)) == 0:
                print("empty file detected: rerunning stage")
                sys.exit("bad dep")
        # run the job, silently
        return True
    else:
        print("stopping the pipeline.  dependencies don't exist")
        sys.exit("no dep")


# handles where to auto-resume the pipeline on a subsequent run
# label: used as a shorthand for paths we expect
# full path: a bypass for when we want to use it for detecting a location that doesn't fall into the normal format (final_results)
# dep: for checking if the job's dependencies are satisfied-> meant to point to the last stage's "final_results"
# logic is: if the full_path has no files (or the job label shortcut to final_results)
#           and the dependencies are ok, start the stage
def check_where_resume(job_label=None, full_path=None, dep_job_path=None):
    check_where_kill(dep_job_path)
    if job_label:
        job_path = os.path.join(job_label, "data", "final_results")
    else:
        job_path = full_path

    print("looking at:", job_path)

    if os.path.exists(job_path):
        file_list = os.listdir(job_path)
        if len(file_list) > 0:
            for item in file_list:
                file_check_path = os.path.join(job_path, item)
                if (os.path.getsize(file_check_path)) == 0:
                    print("empty file detected: rerunning stage")
                    return False
            print("bypassing!")
            return True
        else:
            print("running")
            return False
    else:
        print("doesn't exist: running")
        return False


def main(config_path, pair_1_path, pair_2_path, single_path, output_folder_path, threads, no_host):
    if not single_path == "":
        read_mode = "single"
        quality_encoding = determine_encoding(single_path)
        print("OPERATING IN SINGLE-ENDED MODE")
    else:
        read_mode = "paired"
        quality_encoding = determine_encoding(pair_1_path)
        print("OPERATING IN PAIRED-MODE")
    if threads == 0:
        thread_count = mp.cpu_count()
    else:
        thread_count = threads
    mp_store = []  # stores the multiprocessing processes

    # --------------------------------------------------
    # profiling vars

    start_time = time.time()
    # the pipeline stages are all labelled.  This is for multiple reasons:  to keep the interim files organized properly
    # and to perform the auto-resume/kill features

    quality_filter_label = "quality_filter"
    host_filter_label = "host_read_filter"
    vector_filter_label = "vector_read_filter"
    rRNA_filter_label = "rRNA_filter"
    repop_job_label = "duplicate_repopulation"
    assemble_contigs_label = "assemble_contigs"
    gene_annotation_BWA_label = "gene_annotation_BWA"
    gene_annotation_BLAT_label = "gene_annotation_BLAT"
    gene_annotation_DIAMOND_label = "gene_annotation_DIAMOND"
    taxon_annotation_label = "taxonomic_annotation"
    ec_annotation_label = "enzyme_annotation"
    network_label = "RPKM_network"
    visualization_label = "visualization"

    # Creates our command object, for creating shellscripts.
    if read_mode == "single":
        commands = mpcom.mt_pipe_commands(Config_path=config_path, Quality_score=quality_encoding, Thread_count=thread_count, sequence_path_1=None, sequence_path_2=None, sequence_signle=single_path)
    elif read_mode == "paired":
        commands = mpcom.mt_pipe_commands(Config_path=config_path, Quality_score=quality_encoding, Thread_count=thread_count, sequence_path_1=pair_1_path, sequence_path_2=pair_2_path, sequence_signle=None)
    paths = mpp.tool_path_obj(config_path)

    # This is the format we use to launch each stage of the pipeline.
    # We start a multiprocess that starts a subprocess.
    # The subprocess is created from the commands object

    # The quality filter stage
    quality_start = time.time()
    quality_path = os.path.join(output_folder_path, quality_filter_label)
    if not check_where_resume(quality_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                quality_filter_label,
                commands.create_quality_control_command(quality_filter_label),
                True
            )
        )
        process.start()  # start the multiprocess
        process.join()  # wait for it to end
    quality_end = time.time()

    # The host read filter stage
    if not no_host:
        host_start = time.time()
        host_path = os.path.join(output_folder_path, host_filter_label)
        if not check_where_resume(host_path, None, quality_path):
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    host_filter_label,
                    commands.create_host_filter_command(host_filter_label, quality_filter_label),
                    True
                )
            )
            process.start()  # start the multiprocess
            process.join()  # wait for it to end
        host_end = time.time()

    # The vector contaminant filter stage
    vector_start = time.time()
    vector_path = os.path.join(output_folder_path, vector_filter_label)
    if no_host:
        if not check_where_resume(vector_path, None, quality_path):
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    vector_filter_label,
                    commands.create_vector_filter_command(vector_filter_label, quality_filter_label),
                    True
                )
            )
            process.start()  # start the multiprocess
            process.join()  # wait for it to end
    else:
        if not check_where_resume(vector_path, None, host_path):
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    vector_filter_label,
                    commands.create_vector_filter_command(vector_filter_label, host_filter_label),
                    True
                )
            )
            process.start()  # start the multiprocess
            process.join()  # wait for it to end
    vector_end = time.time()

    # rRNA removal stage
    rRNA_filter_start = time.time()

    rRNA_filter_path = os.path.join(output_folder_path, rRNA_filter_label)
    rRNA_filter_singletons_fastq_folder = os.path.join(output_folder_path, "rRNA_filter", "data", "singletons", "singletons_fastq")
    rRNA_filter_pair_1_fastq_folder = os.path.join(output_folder_path, "rRNA_filter", "data", "pair_1", "pair_1_fastq")
    rRNA_filter_pair_2_fastq_folder = os.path.join(output_folder_path, "rRNA_filter", "data", "pair_2", "pair_2_fastq")

    if not check_where_resume(rRNA_filter_path, None, vector_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                rRNA_filter_label,
                commands.create_rRNA_filter_prep_command(
                    rRNA_filter_label, int(mp.cpu_count() / 2), vector_filter_label), #infernal can't take more than 20 extra threads for some reason.
                True
            )
        )
        process.start()
        process.join()

        singletons_mRNA_path = os.path.join(rRNA_filter_path, "data", "singletons", "singletons_mRNA")
        if not check_where_resume(singletons_mRNA_path, None):
            for item in os.listdir(rRNA_filter_singletons_fastq_folder):
                file_root_name = os.path.splitext(item)[0]
                inner_name = file_root_name + "_infernal"
                process = mp.Process(
                    target=commands.create_and_launch,
                    args=(
                        "rRNA_filter",
                        commands.create_rRNA_filter_command("rRNA_filter", "singletons", file_root_name),
                        True,
                        inner_name
                    )
                )
                process.start()
                mp_store.append(process)  # pack all the processes into a list
        for item in mp_store:
            item.join()  # wait for things to finish
        mp_store[:] = []  # clear the list

        if read_mode == "paired":
            pair_1_mRNA_path = os.path.join(rRNA_filter_path, "data", "pair_1", "pair_1_mRNA")
            if not check_where_resume(pair_1_mRNA_path, None):
                for item in os.listdir(rRNA_filter_pair_1_fastq_folder):
                    file_root_name = os.path.splitext(item)[0]
                    inner_name = file_root_name + "_infernal"
                    process = mp.Process(
                        target=commands.create_and_launch,
                        args=(
                            "rRNA_filter",
                            commands.create_rRNA_filter_command("rRNA_filter", "pair_1", file_root_name),
                            True,
                            inner_name
                        )
                    )
                    process.start()
                    mp_store.append(process)
            for item in mp_store:
                item.join()  # wait for things to finish
            mp_store[:] = []  # clear the list

            pair_2_mRNA_path = os.path.join(rRNA_filter_path, "data", "pair_2", "pair_2_mRNA")
            if not check_where_resume(pair_2_mRNA_path, None):
                for item in os.listdir(rRNA_filter_pair_2_fastq_folder):
                    file_root_name = os.path.splitext(item)[0]
                    inner_name = file_root_name + "_infernal"
                    process = mp.Process(
                        target=commands.create_and_launch,
                        args=(
                            "rRNA_filter",
                            commands.create_rRNA_filter_command("rRNA_filter", "pair_2", file_root_name),
                            True,
                            inner_name
                        )
                    )
                    process.start()
                    mp_store.append(process)
            for item in mp_store:
                item.join()  # wait for things to finish
            mp_store[:] = []  # clear the list

        inner_name = "rRNA_filter_post"
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                rRNA_filter_label,
                commands.create_rRNA_filter_post_command(rRNA_filter_label),
                True,
                inner_name
            )
        )
        process.start()
        process.join()

    rRNA_filter_end = time.time()
    # -------------------------------------------------------------
    # Duplicate repopulation
    repop_start = time.time()
    repop_job_path = os.path.join(output_folder_path, repop_job_label)
    if not check_where_resume(repop_job_path, None, rRNA_filter_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                repop_job_label,
                commands.create_repop_command(repop_job_label, quality_filter_label, rRNA_filter_label),
                True
            )
        )
        process.start()
        process.join()
    repop_end = time.time()
    # ----------------------------------------
    # Assemble contigs
    assemble_contigs_start = time.time()
    assemble_contigs_path = os.path.join(output_folder_path, assemble_contigs_label)
    if not check_where_resume(assemble_contigs_path, None, repop_job_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                assemble_contigs_label,
                commands.create_assemble_contigs_command(assemble_contigs_label, repop_job_label),
                True
            )
        )
        process.start()
        process.join()
    assemble_contigs_end = time.time()

    # ----------------------------------------------
    # BWA gene annotation
    GA_BWA_start = time.time()
    gene_annotation_BWA_path = os.path.join(output_folder_path, gene_annotation_BWA_label)
    if not check_where_resume(gene_annotation_BWA_path, None, assemble_contigs_path):

        sections = ["contigs", "singletons"]
        if read_mode == "paired":
            sections.extend(["pair_1", "pair_2"])
        for section in sections:
            inner_name = "BWA_" + section
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    gene_annotation_BWA_label,
                    commands.create_BWA_annotate_command(gene_annotation_BWA_label, assemble_contigs_label, section),
                    True,
                    inner_name
                )
            )
            process.start()
            mp_store.append(process)

        for item in mp_store:
            item.join()
        mp_store[:] = []  # clear the list

        inner_name = "BWA_pp"
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                gene_annotation_BWA_label,
                commands.create_BWA_pp_command(gene_annotation_BWA_label, assemble_contigs_label),
                True,
                inner_name
            )
        )
        process.start()
        process.join()
    GA_BWA_end = time.time()

    # ------------------------------------------------
    # BLAT gene annotation
    GA_BLAT_start = time.time()
    gene_annotation_BLAT_path = os.path.join(output_folder_path, gene_annotation_BLAT_label)
    if not check_where_resume(gene_annotation_BLAT_path, None, gene_annotation_BWA_path):

        BlatPool = mp.Pool(int(thread_count / 2))
        sections = ["contigs", "singletons"]
        if read_mode == "paired":
            sections.extend(["pair_1", "pair_2"])
        for section in sections:
            for fasta_db in os.listdir(paths.DNA_DB_Split):
                if fasta_db.endswith(".fasta") or fasta_db.endswith(".ffn") or fasta_db.endswith(".fsa") or fasta_db.endswith(".fas") or fasta_db.endswith(".fna") or fasta_db.endswith(".ffn"):
                    inner_name = "BLAT_" + section + "_" + fasta_db
                    BlatPool.apply_async(commands.create_and_launch,
                                         args=(
                                             gene_annotation_BLAT_label,
                                             commands.create_BLAT_annotate_command(gene_annotation_BLAT_label, gene_annotation_BWA_label, section, fasta_db),
                                             True,
                                             inner_name
                                         )
                                         )
        BlatPool.close()
        BlatPool.join()

        for section in sections:
            inner_name = section + "_cat"
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    gene_annotation_BLAT_label,
                    commands.create_BLAT_cat_command(gene_annotation_BLAT_label, section),
                    True,
                    inner_name
                )
            )
            process.start()
            mp_store.append(process)
        for item in mp_store:
            item.join()
        mp_store[:] = []

        inner_name = "BLAT_pp"
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                gene_annotation_BLAT_label,
                commands.create_BLAT_pp_command(gene_annotation_BLAT_label, gene_annotation_BWA_label),
                True,
                inner_name
            )
        )
        process.start()
        process.join()
    GA_BLAT_end = time.time()

    # ------------------------------------------------------
    # Diamond gene annotation
    GA_DIAMOND_start = time.time()
    gene_annotation_DIAMOND_path = os.path.join(output_folder_path, gene_annotation_DIAMOND_label)
    if not check_where_resume(gene_annotation_DIAMOND_path, None, gene_annotation_BLAT_path):

        sections = ["contigs", "singletons"]
        if read_mode == "paired":
            sections.extend(["pair_1", "pair_2"])
        for section in sections:
            inner_name = section + "_run_diamond"
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    gene_annotation_DIAMOND_label,
                    commands.create_DIAMOND_annotate_command(gene_annotation_DIAMOND_label, gene_annotation_BLAT_label, section),
                    True,
                    inner_name
                )
            )
            process.start()
            mp_store.append(process)
        for item in mp_store:
            item.join()
        mp_store[:] = []

        inner_name = "diamond_pp"
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                gene_annotation_DIAMOND_label,
                commands.create_DIAMOND_pp_command(gene_annotation_DIAMOND_label, gene_annotation_BLAT_label),
                True,
                inner_name
            )
        )
        process.start()
        process.join()
    GA_DIAMOND_end = time.time()
    # ------------------------------------------------------
    # Taxonomic annotation
    TA_start = time.time()
    taxon_annotation_path = os.path.join(output_folder_path, taxon_annotation_label)
    if not check_where_resume(taxon_annotation_path, None, gene_annotation_DIAMOND_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                taxon_annotation_label,
                commands.create_taxonomic_annotation_command(taxon_annotation_label, assemble_contigs_label, gene_annotation_DIAMOND_label),
                True
            )
        )
        process.start()
        process.join()
    TA_end = time.time()

    # ------------------------------------------------------
    # Detect EC annotation
    EC_start = time.time()
    EC_DETECT_start = time.time()
    ec_annotation_path = os.path.join(output_folder_path, ec_annotation_label)
    if not check_where_resume(ec_annotation_path, None, gene_annotation_DIAMOND_path):
        # Preparing folders for DETECT
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                ec_annotation_label,
                commands.create_EC_DETECT_prep(ec_annotation_label, gene_annotation_DIAMOND_label, int(mp.cpu_count() / 2)),
                True
            )
        )
        process.start()
        process.join()

        # Running DETECT on split protein files
        proteins_path = os.path.join(output_folder_path, ec_annotation_label, "data", "0_proteins")
        for item in os.listdir(proteins_path):
            file_root_name = os.path.splitext(item)[0]
            inner_name = file_root_name + "_detect"
            process = mp.Process(
                target=commands.create_and_launch,
                args=(
                    ec_annotation_label,
                    commands.create_EC_DETECT_command(ec_annotation_label, file_root_name),
                    True,
                    inner_name
                )
            )
            process.start()
            mp_store.append(process)  # pack all the processes into a list

        for item in mp_store:
            item.join()  # wait for things to finish
        mp_store[:] = []  # clear the list
    EC_DETECT_end = time.time()

    # --------------------------------------------------------------
    # Priam and Diamond EC annotation
    EC_PRIAM_DIAMOND_start = time.time()
    if not check_where_resume(ec_annotation_path, None, gene_annotation_DIAMOND_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                ec_annotation_label,
                commands.create_EC_PRIAM_DIAMOND_command(ec_annotation_label, gene_annotation_DIAMOND_label),
                True
            )
        )
        process.start()
        process.join()

        inner_name = "ea_post"
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                ec_annotation_label,
                commands.create_EC_postprocess_command(ec_annotation_label, gene_annotation_DIAMOND_label),
                True,
                inner_name
            )
        )
        process.start()
        process.join()
    EC_PRIAM_DIAMOND_end = time.time()
    EC_end = time.time()

    # ------------------------------------------------------
    # RPKM Table and Cytoscape Network
    Cytoscape_start = time.time()
    network_path = os.path.join(output_folder_path, network_label)
    if not check_where_resume(network_path, None, ec_annotation_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                network_label,
                commands.create_Network_generation_command(network_label, gene_annotation_DIAMOND_label, taxon_annotation_label, ec_annotation_label),
                True
            )
        )
        process.start()
        process.join()
    Cytoscape_end = time.time()

    # ------------------------------------------------------
    # Final Pie Charts
    Chart_start = time.time()
    visualization_path = os.path.join(output_folder_path, visualization_label)
    if not check_where_resume(visualization_path, None, network_path):
        process = mp.Process(
            target=commands.create_and_launch,
            args=(
                visualization_label,
                commands.create_visualization_command(visualization_label, network_label),
                True
            )
        )
        process.start()
        process.join()
    Chart_end = time.time()

    end_time = time.time()
    print("Total runtime:", '%1.1f' % (end_time - start_time), "s")
    print("quality filter:", '%1.1f' % (quality_end - quality_start), "s")
    if not no_host:
        print("host filter:", '%1.1f' % (host_end - host_start), "s")
    print("vector filter:", '%1.1f' % (vector_end - vector_start), "s")
    print("rRNA filter:", '%1.1f' % (rRNA_filter_end - rRNA_filter_start), "s")
    print("repop:", '%1.1f' % (repop_end - repop_start), "s")
    print("assemble contigs:", '%1.1f' % (assemble_contigs_end - assemble_contigs_start), "s")
    print("GA BWA:", '%1.1f' % (GA_BWA_end - GA_BWA_start), "s")
    print("GA BLAT:", '%1.1f' % (GA_BLAT_end - GA_BLAT_start), "s")
    print("GA DIAMOND:", '%1.1f' % (GA_DIAMOND_end - GA_DIAMOND_start), "s")
    print("TA:", '%1.1f' % (TA_end - TA_start), "s")
    print("EC DETECT:", '%1.1f' % (EC_DETECT_end - EC_DETECT_start), "s")
    print("EC PRIAM + DIAMOND:", '%1.1f' % (EC_PRIAM_DIAMOND_end - EC_PRIAM_DIAMOND_start), "s")
    print("Cytoscape:", '%1.1f' % (Cytoscape_end - Cytoscape_start), "s")
    print("Charts: ", '%1.1f' % (Chart_end - Chart_start), "s")


if __name__ == "__main__":
    # This is where the code starts
    # There's a few operating modes, mainly "docker", and "singularity".  These modes edit the pipeline filepaths

    parser = ArgumentParser(description="MetaPro - Meta-omic sequence processing and analysis pipeline"
                                        "Version 1.0 © 2018")

    parser.add_argument("-c", "--config", type=str,
                        help="Path to the configureation file")
    parser.add_argument("-1", "--pair1", type=str,
                        help="Path to the file containing the forward paired-end reads in fastq format")
    parser.add_argument("-2", "--pair2", type=str,
                        help="Path to the file containing the reverse paired-end reads in fastq format")
    parser.add_argument("-s", "--single", type=str,
                        help="Path to the file containing the single-end reads in fastq format")
    parser.add_argument("-o", "--output_folder", type=str, required=True,
                        help="Path of the folder for the output of the pipeline")
    parser.add_argument("-t", "--num_threads", type=int,
                        help="Maximum number of threads used by the pipeline")
    parser.add_argument("--nhost", action='store_true',
                        help="Skip the host read removal step of the pipeline")

    args = parser.parse_args()

    if (args.pair1 and not args.pair2) or (args.pair2 and not args.pair1):
        print("You must specify both forward and reverse reads for a paired-end run")
        sys.exit()
    elif args.single and (args.pair1 or args.pair2):
        print("You cannot specify both paired-end and single-end reads in a single run.")
        sys.exit()

    config_file = args.config if args.pair1 else ""
    pair_1 = args.pair1 if args.pair1 else ""
    pair_2 = args.pair2 if args.pair2 else ""
    single = args.single if args.single else ""
    output_folder = args.output_folder
    num_threads = args.num_threads if args.num_threads else 0
    no_host = args.nhost if args.nhost else False

    if not (os.path.exists(output_folder)):
        print("output folder does not exist.  Now building directory.")
        os.makedirs(output_folder)
    os.chdir(output_folder)

    config = ConfigParser()
    if args.config:
        config.read(config_file)
        if not args.pair1 and not args.pair2 and not args.single:
            pair_1 = config["Sequences"]["pair1"] if config["Sequences"]["pair1"] else ""
            pair_2 = config["Sequences"]["pair2"] if config["Sequences"]["pair2"] else ""
            single = config["Sequences"]["single"] if config["Sequences"]["single"] else ""

    if pair_1 == "" and pair_2 == "" and single == "":
        print("You must specify paired-end or single-end reads as input for the pipeline.")
        sys.exit()

    main(config_file, pair_1, pair_2, single, output_folder, num_threads, no_host)