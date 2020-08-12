# The functions here generate the pipeline commands.
# The functions here generate the pipeline commands.
# Each command module is made up of sub stages that are used to get the final result.

import os
import os.path
import MetaPro_paths as mpp
import subprocess as sp
import time
from datetime import datetime as dt

class mt_pipe_commands:
    # --------------------------------------------------------------------
    # constructor:
    # there should only be one of these objects used for an entire pipeline.
    def __init__(self, no_host, Config_path, Quality_score=33, Thread_count=8, chunk_size = 100000, sequence_path_1=None, sequence_path_2=None, sequence_single=None):

        self.tool_path_obj = mpp.tool_path_obj(Config_path)
        self.no_host_flag = no_host

        # path to the genome sequence file
        if sequence_single is not None:
            self.sequence_single = sequence_single
            self.sequence_path_1 = ""
            self.sequence_path_2 = ""
            print("Reads:", self.sequence_single)
            self.read_mode = "single"
        else:
            self.sequence_single = ""
            self.sequence_path_1 = sequence_path_1
            self.sequence_path_2 = sequence_path_2
            print("Forward Reads:", self.sequence_path_1)
            print("Reverse Reads:", self.sequence_path_2)
            self.read_mode = "paired"

        self.Qual_str = str(Quality_score)
        self.Output_Path = os.getcwd()
        self.Threads_str = str(Thread_count)
        self.rRNA_chunks = str(chunk_size)
        self.chunk_size = str(chunk_size)

        print("Output filepath:", self.Output_Path)

    # -----------------------------------------------------------
    # support functions
    def make_folder(self, folder_path):
        if not (os.path.exists(folder_path)):
            os.makedirs(folder_path)

    def create_and_launch(self, job_name, command_list, run_job=False, inner_name=None):#, work_in_background=False):
        # create the pbs job, and launch items
        # job name: string tag for export file name
        # command list:  list of command statements for writing
        # mode: selection of which pbs template to use: default -> low memory
        # dependency_list: if not empty, will append wait args to sbatch subprocess call. it's polymorphic
        # returns back the job ID given from sbatch

        # docker mode: single cpu
        # no ID, no sbatch.  just run the command
        
        shell_script_full_path = os.path.join(self.Output_Path, job_name, job_name + ".sh")
        
        #sys.stdout = open(shell_script_full_path + ".out", "w")
        tool_output_path = os.path.join(self.Output_Path, job_name, job_name + "_tool_output.txt")
        if inner_name is not None:
            shell_script_full_path = os.path.join(self.Output_Path, job_name, inner_name + ".sh")
            tool_output_path = os.path.join(self.Output_Path, job_name, inner_name + "_tool_output.txt")
        with open(shell_script_full_path, "w") as PBS_script_out:
            for item in command_list:
                PBS_script_out.write(item + "\n")
            PBS_script_out.close()
        if run_job:
            #if not work_in_background:
            output = ""
            try:
                #output = sp.check_output(["sh", shell_script_full_path], stderr = sp.STDOUT)
                #full_command = shell_script_full_path + " > " + shell_script_full_path + ".out 2&>1"
                #out = sp.check_output(["sh", shell_script_full_path], stderr = sp.STDOUT) #, " > " + shell_script_full_path + ".out 2>&1"])#, stderr = sp.STDOUT)
                #out = sp.getoutput(["sh", shell_script_full_path])
                #out_file = shell_script_full_path + ".out"
                #with open(out_file, "w") as job_out:
                #    for item in out:
                #        job_out.write(item + "\n")
                sp.check_output(["sh", shell_script_full_path])#, stderr = sp.STDOUT)
            except sp.CalledProcessError as e:
                return_code = e.returncode
                if return_code != 1:
                    raise
            #with open(tool_output_path, "w") as tool_output:
            #    for line in output:
            #        tool_output.write(line + "\n")
            # else:
                # try:
                    # process_id = sp.Popen(["sh", shell_script_full_path], stderr = sp.STDOUT)
                    # return process_id
                # except sp.CalledProcessError as e:
                    # return_code = e.returncode
                    # if return_code != 1:
                        # raise
        else:
            print("not running job.  run_job set to False")
    
    def launch_only(self, command_list, command_list_length):
        #just launch the job.  Don't make a script file.
        #print(dt.today(), "inside launch_only:", len(command_list))
        
        if(command_list_length == 1):
            #print("0th item:", command_list[0])
            try:
                os.system(command_list[0])
            except sp.CalledProcessError as e:
                return_code = e.returncode
                if return_code != 1:
                    raise
        else:
        
            for command_item in command_list:
                try:
                    os.system(command_item)
                except sp.CalledProcessError as e:
                    return_code = e.returncode
                    if return_code != 1:
                        raise
                
    def create_quality_control_command(self, stage_name):
        subfolder                   = os.path.join(self.Output_Path, stage_name)
        data_folder                 = os.path.join(subfolder, "data")
        sorted_read_folder          = os.path.join(data_folder, "0_sorted_raw_input")
        adapter_folder              = os.path.join(data_folder, "1_adapter_removal")
        tag_remove_folder           = os.path.join(data_folder, "2_tag_remove")
        vsearch_merge_folder        = os.path.join(data_folder, "3_vsearch_pair_merge")
        vsearch_filter_folder       = os.path.join(data_folder, "4_quality_filter")
        orphan_read_filter_folder   = os.path.join(data_folder, "5_orphan_read_filter")
        cdhit_folder                = os.path.join(data_folder, "6_remove_duplicates")
        final_folder                = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(sorted_read_folder)
        self.make_folder(adapter_folder)
        self.make_folder(tag_remove_folder)
        self.make_folder(vsearch_merge_folder)
        self.make_folder(vsearch_filter_folder)
        self.make_folder(orphan_read_filter_folder)
        self.make_folder(cdhit_folder)
        self.make_folder(final_folder)
        
        sort_pair_1 = ">&2 echo Sorting pair 1 | "
        sort_pair_1 += self.tool_path_obj.Python + " "
        sort_pair_1 += self.tool_path_obj.sort_reads + " "
        sort_pair_1 += self.sequence_path_1 + " "
        sort_pair_1 += os.path.join(sorted_read_folder, "pair_1_sorted.fastq") + " "
        sort_pair_1 += "forward"

        sort_pair_2 = ">&2 echo Sorting pair 2 | "
        sort_pair_2 += self.tool_path_obj.Python + " "
        sort_pair_2 += self.tool_path_obj.sort_reads + " "
        sort_pair_2 += self.sequence_path_2 + " "
        sort_pair_2 += os.path.join(sorted_read_folder, "pair_2_sorted.fastq") + " "
        sort_pair_2 += "reverse"

        adapter_removal_line = ">&2 echo Removing adapters | "
        adapter_removal_line += self.tool_path_obj.AdapterRemoval
        if self.read_mode == "single":
            adapter_removal_line += " --file1 " + self.sequence_single
        elif self.read_mode == "paired":
            adapter_removal_line += " --file1 " + os.path.join(sorted_read_folder, "pair_1_sorted.fastq")
            adapter_removal_line += " --file2 " + os.path.join(sorted_read_folder, "pair_2_sorted.fastq")
        adapter_removal_line += " --qualitybase " + str(self.Qual_str)
        if(self.Qual_str == "33"):
            adapter_removal_line += " --qualitymax 75"
        adapter_removal_line += " --threads " + self.Threads_str
        adapter_removal_line += " --minlength " + str(self.tool_path_obj.adapterremoval_minlength)
        adapter_removal_line += " --basename " + adapter_folder
        adapter_removal_line += "_AdapterRemoval"
        adapter_removal_line += " --trimqualities "
        if self.read_mode == "single":
            adapter_removal_line += " --output1 " + os.path.join(adapter_folder, "singletons_adptr_rem.fastq")
        elif self.read_mode == "paired":
            adapter_removal_line += " --output1 " + os.path.join(adapter_folder, "pair_1_adptr_rem.fastq")
            adapter_removal_line += " --output2 " + os.path.join(adapter_folder, "pair_2_adptr_rem.fastq")
            adapter_removal_line += " --singleton " + os.path.join(adapter_folder, "singletons_adptr_rem.fastq")

        #Sort-reads introduces tags at the read-level of the 
        tag_remove_pair_1 = ">&2 echo Remove tags pair 1 | "
        tag_remove_pair_1 += self.tool_path_obj.Python + " "
        tag_remove_pair_1 += self.tool_path_obj.remove_tag + " "
        tag_remove_pair_1 += os.path.join(adapter_folder, "pair_1_adptr_rem.fastq") + " "
        tag_remove_pair_1 += os.path.join(tag_remove_folder, "pair_1_no_tags.fastq")
        
        tag_remove_pair_2 = ">&2 echo Remove tags pair 2 | "
        tag_remove_pair_2 += self.tool_path_obj.Python + " "
        tag_remove_pair_2 += self.tool_path_obj.remove_tag + " "
        tag_remove_pair_2 += os.path.join(adapter_folder, "pair_2_adptr_rem.fastq") + " "
        tag_remove_pair_2 += os.path.join(tag_remove_folder, "pair_2_no_tags.fastq")

        tag_remove_singletons =  ">&2 echo Remove tags singletons | " 
        tag_remove_singletons += self.tool_path_obj.Python + " "
        tag_remove_singletons += self.tool_path_obj.remove_tag + " "
        tag_remove_singletons += os.path.join(adapter_folder, "singletons_adptr_rem.fastq") + " "
        tag_remove_singletons += os.path.join(tag_remove_folder, "singletons_no_tags.fastq")
        # tries to merge the cleaned pairs
        # rejects get sent out
        vsearch_merge = ">&2 echo " + "Vsearch Merge pairs | "
        vsearch_merge += self.tool_path_obj.vsearch
        vsearch_merge += " --fastq_mergepairs " + os.path.join(tag_remove_folder, "pair_1_no_tags.fastq")
        vsearch_merge += " --reverse " + os.path.join(tag_remove_folder, "pair_2_no_tags.fastq")
        vsearch_merge += " --fastq_ascii " + str(self.Qual_str)
        vsearch_merge += " --fastqout " + os.path.join(vsearch_merge_folder, "merge_success.fastq")
        vsearch_merge += " --fastqout_notmerged_fwd " + os.path.join(vsearch_merge_folder, "pair_1_merge_reject.fastq")
        vsearch_merge += " --fastqout_notmerged_rev " + os.path.join(vsearch_merge_folder, "pair_2_merge_reject.fastq")

        # concatenate the merge overlaps with the singletons
        cat_glue = ">&2 echo concatenating singletons | "
        cat_glue += "cat "
        cat_glue += os.path.join(vsearch_merge_folder, "merge_success.fastq") + " "
        cat_glue += os.path.join(tag_remove_folder, "singletons_no_tags.fastq")
        cat_glue += " > " + os.path.join(vsearch_merge_folder, "singletons.fastq")

        # Filter out low-quality reads
        # start with the singles / merged sections
        
        vsearch_filter_0 = ">&2 echo low-quality filter on singletons | "
        vsearch_filter_0 += self.tool_path_obj.vsearch
        if self.read_mode == "single":
            vsearch_filter_0 += " --fastq_filter " + os.path.join(adapter_folder, "singletons_adptr_rem.fastq")
        elif self.read_mode == "paired":
            vsearch_filter_0 += " --fastq_filter " + os.path.join(vsearch_merge_folder, "singletons.fastq")
        vsearch_filter_0 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_0 += " --fastq_maxee " + "2.0"
        vsearch_filter_0 += " --fastqout " + os.path.join(vsearch_filter_folder, "singletons_hq.fastq")

        # then move onto the standalones in pair 1
        vsearch_filter_1 = ">&2 echo low-quality filter on pair 1 | "
        vsearch_filter_1 += self.tool_path_obj.vsearch
        vsearch_filter_1 += " --fastq_filter " + os.path.join(vsearch_merge_folder, "pair_1_merge_reject.fastq")
        vsearch_filter_1 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_1 += " --fastq_maxee " + "2.0"
        vsearch_filter_1 += " --fastqout " + os.path.join(vsearch_filter_folder, "pair_1_hq.fastq")

        vsearch_filter_2 = ">&2 echo low-quality filter on pair 2 | "
        vsearch_filter_2 += self.tool_path_obj.vsearch
        vsearch_filter_2 += " --fastq_filter " + os.path.join(vsearch_merge_folder, "pair_2_merge_reject.fastq")
        vsearch_filter_2 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_2 += " --fastq_maxee " + "2.0"
        vsearch_filter_2 += " --fastqout " + os.path.join(vsearch_filter_folder, "pair_2_hq.fastq")

        # redistribute data into singletons, or paired-reads
        orphan_read_filter = ">&2 echo moving newly orphaned reads | "
        orphan_read_filter += self.tool_path_obj.Python + " "
        orphan_read_filter += self.tool_path_obj.orphaned_read_filter + " "
        orphan_read_filter += os.path.join(vsearch_filter_folder, "pair_1_hq.fastq") + " "
        orphan_read_filter += os.path.join(vsearch_filter_folder, "pair_2_hq.fastq") + " "
        orphan_read_filter += os.path.join(vsearch_filter_folder, "singletons_hq.fastq") + " "
        orphan_read_filter += os.path.join(orphan_read_filter_folder, "pair_1_match.fastq") + " "
        orphan_read_filter += os.path.join(orphan_read_filter_folder, "pair_2_match.fastq") + " "
        orphan_read_filter += os.path.join(orphan_read_filter_folder, "singletons_with_duplicates.fastq")

        # remove duplicates (to shrink the data size)
        cdhit_singletons = ">&2 echo removing singleton duplicates | "
        cdhit_singletons += self.tool_path_obj.cdhit_dup + " -i "
        if self.read_mode == "single":
            cdhit_singletons += os.path.join(vsearch_filter_folder, "singletons_hq.fastq")
        elif self.read_mode == "paired":
            cdhit_singletons += os.path.join(orphan_read_filter_folder, "singletons_with_duplicates.fastq")
        cdhit_singletons += " -o " + os.path.join(cdhit_folder, "singletons_unique.fastq")

        # remove duplicates in the pairs
        cdhit_paired = ">&2 echo remove duplicates from paired | "
        cdhit_paired += self.tool_path_obj.cdhit_dup
        cdhit_paired += "-i"    + " " + os.path.join(orphan_read_filter_folder, "pair_1_match.fastq") + " "
        cdhit_paired += "-i2"   + " " + os.path.join(orphan_read_filter_folder, "pair_2_match.fastq") + " "
        cdhit_paired += "-o"    + " " + os.path.join(cdhit_folder, "pair_1_unique.fastq") + " "
        cdhit_paired += "-o2"   + " " + os.path.join(cdhit_folder, "pair_2_unique.fastq")

        #move data to appropriate places
        copy_singletons = "cp " + os.path.join(cdhit_folder, "singletons_unique.fastq") + " "
        copy_singletons += os.path.join(final_folder, "singletons.fastq")

        copy_pair_1 = "cp " + os.path.join(cdhit_folder, "pair_1_unique.fastq") + " "
        copy_pair_1 += os.path.join(final_folder, "pair_1.fastq")

        copy_pair_2 = "cp " + os.path.join(cdhit_folder, "pair_2_unique.fastq") + " "
        copy_pair_2 += os.path.join(final_folder, "pair_2.fastq")
        
        # move these particular files to final_folder because they'll be needed by another stage.
        copy_duplicate_singletons = "cp "
        if(self.read_mode == "single"):
            copy_duplicate_singletons += os.path.join(vsearch_filter_folder, "singletons_hq.fastq") + " "
            copy_duplicate_singletons += os.path.join(final_folder, "singletons_hq.fastq")
        else:
            copy_duplicate_singletons += os.path.join(orphan_read_filter_folder, "singletons_with_duplicates.fastq") + " "
            copy_duplicate_singletons += os.path.join(final_folder, "singletons_with_duplicates.fastq")

        copy_pair_1_match = "cp " + os.path.join(orphan_read_filter_folder, "pair_1_match.fastq") + " "
        copy_pair_1_match += os.path.join(final_folder, "pair_1_match.fastq")

        copy_pair_2_match = "cp " + os.path.join(orphan_read_filter_folder, "pair_2_match.fastq") + " "
        copy_pair_2_match += os.path.join(final_folder, "pair_2_match.fastq")

        copy_singletons_cluster = "cp " + os.path.join(cdhit_folder, "singletons_unique.fastq.clstr") + " "
        copy_singletons_cluster += os.path.join(final_folder, "singletons_unique.fastq.clstr")

        copy_paired_cluster = "cp " + os.path.join(cdhit_folder, "pair_1_unique.fastq.clstr") + " "
        copy_paired_cluster += os.path.join(final_folder, "pair_1_unique.fastq.clstr")

        if self.read_mode == "single":
            COMMANDS_qual = [
                adapter_removal_line,
                vsearch_filter_0,
                cdhit_singletons,
                copy_singletons,
                copy_duplicate_singletons,
                copy_singletons_cluster
            ]
        elif self.read_mode == "paired":
            COMMANDS_qual = [
                sort_pair_1,
                sort_pair_2,
                adapter_removal_line,
                tag_remove_pair_1,
                tag_remove_pair_2,
                tag_remove_singletons,
                vsearch_merge,
                cat_glue,
                vsearch_filter_0,
                vsearch_filter_1,
                vsearch_filter_2,
                orphan_read_filter,
                cdhit_singletons,
                cdhit_pair_1,
                cdhit_pair_2,
                copy_singletons,
                copy_pair_1,
                copy_pair_2,
                copy_duplicate_singletons,
                copy_singletons_cluster,
                copy_pair_1_match,
                copy_pair_1_cluster,
                copy_pair_2_match,
                copy_pair_2_cluster
            ]

        return COMMANDS_qual

    def create_host_filter_command(self, stage_name, dependency_name):
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        quality_folder      = os.path.join(self.Output_Path, dependency_name, "final_results")
        host_removal_folder = os.path.join(data_folder, "0_remove_host")
        blat_hr_folder      = os.path.join(data_folder, "1_blat_host")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(host_removal_folder)
        self.make_folder(blat_hr_folder)
        self.make_folder(final_folder)

        Host_Contaminants = os.path.join(host_removal_folder, "host_contaminents_seq.fasta")
        copy_host = ">&2 echo Copy the host file over | "
        copy_host += "cp " + self.tool_path_obj.Host + " " + Host_Contaminants

        # craft a BWA index for the host sequences
        bwa_hr_prep = ">&2 echo make host contaminants index for BWA | "
        bwa_hr_prep += self.tool_path_obj.BWA + " index -a bwtsw " + Host_Contaminants

        samtools_hr_prep = ">&2 echo SAMTOOLS host contaminant prep | "
        samtools_hr_prep += self.tool_path_obj.SAMTOOLS + " faidx " + Host_Contaminants

        # host removal on unique singletons
        bwa_hr_singletons = ">&2 echo BWA host remove on singletons | "
        bwa_hr_singletons += self.tool_path_obj.BWA + " mem -t "
        bwa_hr_singletons += self.Threads_str + " "
        bwa_hr_singletons += Host_Contaminants + " "
        bwa_hr_singletons += os.path.join(quality_folder, "singletons.fastq")
        bwa_hr_singletons += " > " + os.path.join(host_removal_folder, "singletons_no_host.sam")

        # annoying type conversion pt 1
        samtools_hr_singletons_sam_to_bam = ">&2 echo convert singletons host reads | "
        samtools_hr_singletons_sam_to_bam += self.tool_path_obj.SAMTOOLS
        samtools_hr_singletons_sam_to_bam += " view -bS " + os.path.join(host_removal_folder, "singletons_no_host.sam")
        samtools_hr_singletons_sam_to_bam += " > " + os.path.join(host_removal_folder, "singletons_no_host.bam")
        # annoying type conversion pt 2
        samtools_no_host_singletons_bam_to_fastq = self.tool_path_obj.SAMTOOLS + " fastq -n -f 4" + " -0 "
        samtools_no_host_singletons_bam_to_fastq += os.path.join(host_removal_folder, "singletons_no_host.fastq") + " "
        samtools_no_host_singletons_bam_to_fastq += os.path.join(host_removal_folder, "singletons_no_host.bam")

        # apparently, we're to keep the host separation
        samtools_host_singletons_bam_to_fastq = self.tool_path_obj.SAMTOOLS + " fastq -n -F 4" + " -0 "
        samtools_host_singletons_bam_to_fastq += os.path.join(host_removal_folder, "singletons_host_only.fastq") + " "
        samtools_host_singletons_bam_to_fastq += os.path.join(host_removal_folder, "singletons_no_host.bam")

        # bwa hr pair 1 only
        bwa_hr_pair_1 = ">&2 echo bwa pair host remove | "
        bwa_hr_pair_1 += self.tool_path_obj.BWA + " mem -t "
        bwa_hr_pair_1 += self.Threads_str + " "
        bwa_hr_pair_1 += Host_Contaminants + " "
        bwa_hr_pair_1 += os.path.join(quality_folder, "pair_1.fastq")
        bwa_hr_pair_1 += " > " + os.path.join(host_removal_folder, "pair_1_no_host.sam")

        # separating bwa results back into paired reads
        samtools_host_pair_1_sam_to_bam = ">&2 echo convert pair host files pt1 | "
        samtools_host_pair_1_sam_to_bam += self.tool_path_obj.SAMTOOLS + " view -bS " + os.path.join(
            host_removal_folder, "pair_1_no_host.sam")
        samtools_host_pair_1_sam_to_bam += " > " + os.path.join(host_removal_folder, "pair_1_no_host.bam")

        # stuff that doesn't match with the host
        samtools_no_host_pair_1_bam_to_fastq = ">&2 echo convert pair host files pt2 | "
        samtools_no_host_pair_1_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -f 4"
        samtools_no_host_pair_1_bam_to_fastq += " -0 " + os.path.join(host_removal_folder, "pair_1_no_host.fastq") + " " # out
        samtools_no_host_pair_1_bam_to_fastq += os.path.join(host_removal_folder, "pair_1_no_host.bam")  # in

        # stuff that matches with the host (why keep it?  request from john)
        samtools_host_pair_1_bam_to_fastq = ">&2 echo convert pair host files pt3 | "
        samtools_host_pair_1_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -F 4"
        samtools_host_pair_1_bam_to_fastq += " -0 " + os.path.join(host_removal_folder, "pair_1_host_only.fastq") + " "
        samtools_host_pair_1_bam_to_fastq += os.path.join(host_removal_folder, "pair_1_no_host.bam")

        # bwa hr pair 1 only
        bwa_hr_pair_2 = ">&2 echo bwa pair host remove | "
        bwa_hr_pair_2 += self.tool_path_obj.BWA + " mem -t "
        bwa_hr_pair_2 += self.Threads_str + " "
        bwa_hr_pair_2 += Host_Contaminants + " "
        bwa_hr_pair_2 += os.path.join(quality_folder, "pair_2.fastq")
        bwa_hr_pair_2 += " > " + os.path.join(host_removal_folder, "pair_2_no_host.sam")

        # separating bwa results back into paired reads
        samtools_host_pair_2_sam_to_bam = ">&2 echo convert pair host files pt1 | "
        samtools_host_pair_2_sam_to_bam += self.tool_path_obj.SAMTOOLS + " view -bS " + os.path.join(
            host_removal_folder, "pair_2_no_host.sam")
        samtools_host_pair_2_sam_to_bam += " > " + os.path.join(host_removal_folder, "pair_2_no_host.bam")

        # stuff that doesn't match with the host
        samtools_no_host_pair_2_bam_to_fastq = ">&2 echo convert pair host files pt2 | "
        samtools_no_host_pair_2_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -f 4"
        samtools_no_host_pair_2_bam_to_fastq += " -0 " + os.path.join(host_removal_folder, "pair_2_no_host.fastq") + " " # out
        samtools_no_host_pair_2_bam_to_fastq += os.path.join(host_removal_folder, "pair_2_no_host.bam")  # in

        # stuff that matches with the host (why keep it?  request from john)
        samtools_host_pair_2_bam_to_fastq = ">&2 echo convert pair host files pt3 | "
        samtools_host_pair_2_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -F 4"
        samtools_host_pair_2_bam_to_fastq += " -0 " + os.path.join(host_removal_folder, "pair_2_host_only.fastq") + " "
        samtools_host_pair_2_bam_to_fastq += os.path.join(host_removal_folder, "pair_2_no_host.bam")

        # blat prep
        make_blast_db_host = ">&2 echo Make BLAST db for host contaminants | "
        make_blast_db_host += self.tool_path_obj.Makeblastdb + " -in " + Host_Contaminants + " -dbtype nucl"

        vsearch_filter_3 = ">&2 echo Convert singletons for BLAT | "
        vsearch_filter_3 += self.tool_path_obj.vsearch
        vsearch_filter_3 += " --fastq_filter " + os.path.join(host_removal_folder, "singletons_no_host.fastq")
        vsearch_filter_3 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_3 += " --fastaout " + os.path.join(host_removal_folder, "singletons_no_host.fasta")

        vsearch_filter_4 = ">&2 echo Convert pair 1 for BLAT | "
        vsearch_filter_4 += self.tool_path_obj.vsearch
        vsearch_filter_4 += " --fastq_filter " + os.path.join(host_removal_folder, "pair_1_no_host.fastq")
        vsearch_filter_4 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_4 += " --fastaout " + os.path.join(host_removal_folder, "pair_1_no_host.fasta")

        vsearch_filter_5 = ">&2 echo Convert pair 2 for BLAT | "
        vsearch_filter_5 += self.tool_path_obj.vsearch
        vsearch_filter_5 += " --fastq_filter " + os.path.join(host_removal_folder, "pair_2_no_host.fastq")
        vsearch_filter_5 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_5 += " --fastaout " + os.path.join(host_removal_folder, "pair_2_no_host.fasta")

        blat_hr_singletons = ">&2 echo BLAT host singletons | "
        blat_hr_singletons += self.tool_path_obj.BLAT + " -noHead -minIdentity=90 -minScore=65 "
        blat_hr_singletons += Host_Contaminants + " "
        blat_hr_singletons += os.path.join(host_removal_folder, "singletons_no_host.fasta")
        blat_hr_singletons += " -fine -q=rna -t=dna -out=blast8 -threads=" + self.Threads_str
        blat_hr_singletons += " " + os.path.join(host_removal_folder, "singletons_no_host.blatout")

        blat_hr_pair_1 = ">&2 echo BLAT host pair 1 | "
        blat_hr_pair_1 += self.tool_path_obj.BLAT
        blat_hr_pair_1 += " -noHead -minIdentity=90 -minScore=65 " + Host_Contaminants + " "
        blat_hr_pair_1 += os.path.join(host_removal_folder, "pair_1_no_host.fasta")
        blat_hr_pair_1 += " -fine -q=rna -t=dna -out=blast8 -threads=" + self.Threads_str
        blat_hr_pair_1 += " " + os.path.join(host_removal_folder, "pair_1_no_host.blatout")

        blat_hr_pair_2 = ">&2 echo BLAT host pair 2 | "
        blat_hr_pair_2 += self.tool_path_obj.BLAT
        blat_hr_pair_2 += " -noHead -minIdentity=90 -minScore=65 " + Host_Contaminants + " "
        blat_hr_pair_2 += os.path.join(host_removal_folder, "pair_2_no_host.fasta")
        blat_hr_pair_2 += " -fine -q=rna -t=dna -out=blast8 -threads=" + self.Threads_str
        blat_hr_pair_2 += " " + os.path.join(host_removal_folder, "pair_2_no_host.blatout")

        # HR BLAT
        hr_singletons = ">&2 echo BLAT contaminant singletons | "
        hr_singletons += self.tool_path_obj.Python + " " + self.tool_path_obj.BLAT_Contaminant_Filter + " "
        hr_singletons += os.path.join(host_removal_folder, "singletons_no_host.fastq") + " "  # in
        hr_singletons += os.path.join(host_removal_folder, "singletons_no_host.blatout") + " "  # in
        hr_singletons += os.path.join(blat_hr_folder, "singletons_no_host.fastq") + " "  # out
        hr_singletons += os.path.join(blat_hr_folder, "singletons_host_only.fastq")  # out

        hr_pair_1 = ">&2 echo BLAT contaminant pair 1 | "
        hr_pair_1 += self.tool_path_obj.Python + " "
        hr_pair_1 += self.tool_path_obj.BLAT_Contaminant_Filter + " "
        hr_pair_1 += os.path.join(host_removal_folder, "pair_1_no_host.fastq") + " "
        hr_pair_1 += os.path.join(host_removal_folder, "pair_1_no_host.blatout") + " "
        hr_pair_1 += os.path.join(blat_hr_folder, "pair_1_no_host.fastq") + " "
        hr_pair_1 += os.path.join(blat_hr_folder, "pair_1_host_only.fastq")

        hr_pair_2 = ">&2 echo BLAT contaminant pair 2 | "
        hr_pair_2 += self.tool_path_obj.Python + " " + self.tool_path_obj.BLAT_Contaminant_Filter + " "
        hr_pair_2 += os.path.join(host_removal_folder, "pair_2_no_host.fastq") + " "
        hr_pair_2 += os.path.join(host_removal_folder, "pair_2_no_host.blatout") + " "
        hr_pair_2 += os.path.join(blat_hr_folder, "pair_2_no_host.fastq") + " "
        hr_pair_2 += os.path.join(blat_hr_folder, "pair_2_host_only.fastq")

        copy_singletons = "cp " + os.path.join(blat_hr_folder, "singletons_no_host.fastq") + " "
        copy_singletons += os.path.join(final_folder, "singletons.fastq")

        copy_pair_1 = "cp " + os.path.join(blat_hr_folder, "pair_1_no_host.fastq") + " "
        copy_pair_1 += os.path.join(final_folder, "pair_1.fastq")

        copy_pair_2 = "cp " + os.path.join(blat_hr_folder, "pair_2_no_host.fastq") + " "
        copy_pair_2 += os.path.join(final_folder, "pair_2.fastq")
        
        data_change_host = ">&2 echo Scanning for relative change in host filtering | " 
        data_change_host += self.tool_path_obj.Python + " "
        data_change_host += self.tool_path_obj.data_change_metrics + " "
        if(self.read_mode == "single"):
            data_change_host += os.path.join(quality_folder, "singletons.fastq") + " "
            data_change_host += os.path.join(final_folder, "singletons.fastq") + " "
            data_change_host += os.path.join(final_folder, "qual_to_host_singletons.tsv")
        elif(self.read_mode == "paired"):
            data_change_host += os.path.join(quality_folder, "pair_1.fastq") + " "
            data_change_host += os.path.join(final_folder, "pair_1.fastq") + " "
            data_change_host += os.path.join(final_folder, "qual_to_host_pair_1.tsv")
        

        if self.read_mode == "single":
            COMMANDS_host = [
                copy_host,
                bwa_hr_prep,
                samtools_hr_prep,
                bwa_hr_singletons,
                samtools_hr_singletons_sam_to_bam,
                samtools_no_host_singletons_bam_to_fastq,
                samtools_host_singletons_bam_to_fastq,
                make_blast_db_host,
                vsearch_filter_3,
                blat_hr_singletons,
                hr_singletons,
                copy_singletons#,
                #data_change_host
            ]
        elif self.read_mode == "paired":
            COMMANDS_host = [
                copy_host,
                bwa_hr_prep,
                samtools_hr_prep,
                bwa_hr_singletons,
                samtools_hr_singletons_sam_to_bam,
                samtools_no_host_singletons_bam_to_fastq,
                samtools_host_singletons_bam_to_fastq,
                bwa_hr_pair_1,
                samtools_host_pair_1_sam_to_bam,
                samtools_no_host_pair_1_bam_to_fastq,
                samtools_host_pair_1_bam_to_fastq,
                bwa_hr_pair_2,
                samtools_host_pair_2_sam_to_bam,
                samtools_no_host_pair_2_bam_to_fastq,
                samtools_host_pair_2_bam_to_fastq,
                make_blast_db_host,
                vsearch_filter_3,
                vsearch_filter_4,
                vsearch_filter_5,
                blat_hr_singletons,
                blat_hr_pair_1,
                blat_hr_pair_2,
                hr_singletons,
                hr_pair_1,
                hr_pair_2,
                copy_singletons,
                copy_pair_1,
                copy_pair_2#,
                #data_change_host
            ]

        return COMMANDS_host

    def create_vector_filter_command(self, stage_name, dependency_name):
        # why do we leave all the interim files intact?
        # because science needs repeatable data, and the process needs to be able to start at any point
        subfolder                       = os.path.join(self.Output_Path, stage_name)
        data_folder                     = os.path.join(subfolder, "data")
        dependency_folder               = os.path.join(self.Output_Path, dependency_name, "final_results")
        vector_removal_folder           = os.path.join(data_folder, "0_vector_removal")
        blat_containment_vector_folder  = os.path.join(data_folder, "1_blat_containment_vr")
        final_folder                    = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(vector_removal_folder)
        self.make_folder(blat_containment_vector_folder)
        self.make_folder(final_folder)

        Vector_Contaminants = os.path.join(vector_removal_folder, "vector_contaminants_seq.fasta")

        copy_vector = ">&2 echo copy vector prep | "
        copy_vector += "cp " + self.tool_path_obj.UniVec_Core + " " + Vector_Contaminants

        bwa_vr_prep = ">&2 echo BWA vector prep | "
        bwa_vr_prep += self.tool_path_obj.BWA + " index -a bwtsw " + Vector_Contaminants

        samtools_vr_prep = ">&2 echo samtools vector prep | "
        samtools_vr_prep += self.tool_path_obj.SAMTOOLS + " faidx " + Vector_Contaminants

        bwa_vr_singletons = ">&2 echo BWA vector oprhans | "
        bwa_vr_singletons += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " "
        bwa_vr_singletons += Vector_Contaminants + " "
        bwa_vr_singletons += os.path.join(dependency_folder, "singletons.fastq")
        bwa_vr_singletons += " > " + os.path.join(vector_removal_folder, "singletons_no_vectors.sam")

        samtools_no_vector_singletons_sam_to_bam = ">&2 echo samtools vector oprhans pt 1 | "
        samtools_no_vector_singletons_sam_to_bam += self.tool_path_obj.SAMTOOLS + " view -bS "
        samtools_no_vector_singletons_sam_to_bam += os.path.join(vector_removal_folder, "singletons_no_vectors.sam")
        samtools_no_vector_singletons_sam_to_bam += " > " + os.path.join(vector_removal_folder,
                                                                         "singletons_no_vectors.bam")

        samtools_no_vector_singletons_bam_to_fastq = ">&2 echo samtools vector singletons pt 2 | "
        samtools_no_vector_singletons_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -f 4"
        samtools_no_vector_singletons_bam_to_fastq += " -0 " + os.path.join(vector_removal_folder,
                                                                            "singletons_no_vectors.fastq") + " "
        samtools_no_vector_singletons_bam_to_fastq += os.path.join(vector_removal_folder, "singletons_no_vectors.bam")

        samtools_vector_singletons_bam_to_fastq = ">&2 echo samtools vector singletons pt 3 | "
        samtools_vector_singletons_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -F 4"
        samtools_vector_singletons_bam_to_fastq += " -0 " + os.path.join(vector_removal_folder,
                                                                         "singletons_vectors_only.fastq") + " "
        samtools_vector_singletons_bam_to_fastq += os.path.join(vector_removal_folder, "singletons_no_vectors.bam")

        bwa_vr_pair_1 = ">&2 echo bwa vector pair | "
        bwa_vr_pair_1 += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " "
        bwa_vr_pair_1 += Vector_Contaminants + " "
        bwa_vr_pair_1 += os.path.join(dependency_folder, "pair_1.fastq") + " "
        bwa_vr_pair_1 += " > " + os.path.join(vector_removal_folder, "pair_1_no_vectors.sam")

        bwa_vr_pair_2 = ">&2 echo bwa vector pair | "
        bwa_vr_pair_2 += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " "
        bwa_vr_pair_2 += Vector_Contaminants + " "
        bwa_vr_pair_2 += os.path.join(dependency_folder, "pair_2.fastq") + " "
        bwa_vr_pair_2 += " > " + os.path.join(vector_removal_folder, "pair_2_no_vectors.sam")

        samtools_vr_pair_1_sam_to_bam = ">&2 echo samtools vector pair pt 1 | "
        samtools_vr_pair_1_sam_to_bam += self.tool_path_obj.SAMTOOLS + " view -bS "
        samtools_vr_pair_1_sam_to_bam += os.path.join(vector_removal_folder, "pair_1_no_vectors.sam")
        samtools_vr_pair_1_sam_to_bam += " > " + os.path.join(vector_removal_folder, "pair_1_no_vectors.bam")

        samtools_no_vector_pair_1_bam_to_fastq = ">&2 echo samtools vector pair pt 2 | "
        samtools_no_vector_pair_1_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -f 4"
        samtools_no_vector_pair_1_bam_to_fastq += " -0 " + os.path.join(vector_removal_folder,
                                                                        "pair_1_no_vectors.fastq")
        samtools_no_vector_pair_1_bam_to_fastq += " " + os.path.join(vector_removal_folder, "pair_1_no_vectors.bam")

        samtools_vector_pair_1_bam_to_fastq = ">&2 echo samtools vector pair pt 3 | "
        samtools_vector_pair_1_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -F 4"
        samtools_vector_pair_1_bam_to_fastq += " -0 " + os.path.join(vector_removal_folder, "pair_1_vectors_only.fastq")
        samtools_vector_pair_1_bam_to_fastq += " " + os.path.join(vector_removal_folder, "pair_1_no_vectors.bam")

        samtools_vr_pair_2_sam_to_bam = ">&2 echo samtools vector pair pt 1 | "
        samtools_vr_pair_2_sam_to_bam += self.tool_path_obj.SAMTOOLS + " view -bS "
        samtools_vr_pair_2_sam_to_bam += os.path.join(vector_removal_folder, "pair_2_no_vectors.sam")
        samtools_vr_pair_2_sam_to_bam += " > " + os.path.join(vector_removal_folder, "pair_2_no_vectors.bam")

        samtools_no_vector_pair_2_bam_to_fastq = ">&2 echo samtools vector pair pt 2 | "
        samtools_no_vector_pair_2_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -f 4"
        samtools_no_vector_pair_2_bam_to_fastq += " -0 " + os.path.join(vector_removal_folder,
                                                                        "pair_2_no_vectors.fastq")
        samtools_no_vector_pair_2_bam_to_fastq += " " + os.path.join(vector_removal_folder, "pair_2_no_vectors.bam")

        samtools_vector_pair_2_bam_to_fastq = ">&2 echo samtools vector pair pt 3 | "
        samtools_vector_pair_2_bam_to_fastq += self.tool_path_obj.SAMTOOLS + " fastq -n -F 4"
        samtools_vector_pair_2_bam_to_fastq += " -0 " + os.path.join(vector_removal_folder, "pair_2_vectors_only.fastq")
        samtools_vector_pair_2_bam_to_fastq += " " + os.path.join(vector_removal_folder, "pair_2_no_vectors.bam")

        make_blast_db_vector = ">&2 echo BLAST make db vectors | "
        make_blast_db_vector += self.tool_path_obj.Makeblastdb + " -in " + Vector_Contaminants + " -dbtype nucl"

        vsearch_filter_6 = ">&2 echo convert vector singletons for BLAT | "
        vsearch_filter_6 += self.tool_path_obj.vsearch
        vsearch_filter_6 += " --fastq_filter " + os.path.join(vector_removal_folder, "singletons_no_vectors.fastq")
        vsearch_filter_6 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_6 += " --fastaout " + os.path.join(vector_removal_folder, "singletons_no_vectors.fasta")

        vsearch_filter_7 = ">&2 echo convert vector pair 1 for BLAT | "
        vsearch_filter_7 += self.tool_path_obj.vsearch
        vsearch_filter_7 += " --fastq_filter " + os.path.join(vector_removal_folder, "pair_1_no_vectors.fastq")
        vsearch_filter_7 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_7 += " --fastaout " + os.path.join(vector_removal_folder, "pair_1_no_vectors.fasta")

        vsearch_filter_8 = ">&2 echo convert vector pair 2 for BLAT | "
        vsearch_filter_8 += self.tool_path_obj.vsearch
        vsearch_filter_8 += " --fastq_filter " + os.path.join(vector_removal_folder, "pair_2_no_vectors.fastq")
        vsearch_filter_8 += " --fastq_ascii " + self.Qual_str
        vsearch_filter_8 += " --fastaout " + os.path.join(vector_removal_folder, "pair_2_no_vectors.fasta")

        blat_vr_singletons = ">&2 echo BLAT vector singletons | "
        blat_vr_singletons += self.tool_path_obj.BLAT
        blat_vr_singletons += " -noHead -minIdentity=90 -minScore=65 "
        blat_vr_singletons += Vector_Contaminants + " "
        blat_vr_singletons += os.path.join(vector_removal_folder, "singletons_no_vectors.fasta")
        blat_vr_singletons += " -fine -q=rna -t=dna -out=blast8 -threads=" + self.Threads_str + " "
        blat_vr_singletons += os.path.join(vector_removal_folder, "singletons_no_vectors.blatout")

        blat_vr_pair_1 = ">&2 echo BLAT vector pair 1 | "
        blat_vr_pair_1 += self.tool_path_obj.BLAT + " -noHead -minIdentity=90 -minScore=65 "
        blat_vr_pair_1 += Vector_Contaminants + " "
        blat_vr_pair_1 += os.path.join(vector_removal_folder, "pair_1_no_vectors.fasta")
        blat_vr_pair_1 += " -fine -q=rna -t=dna -out=blast8 -threads=" + self.Threads_str + " "
        blat_vr_pair_1 += os.path.join(vector_removal_folder, "pair_1_no_vectors.blatout")

        blat_vr_pair_2 = ">&2 echo BLAT vector pair 2 | "
        blat_vr_pair_2 += self.tool_path_obj.BLAT + " -noHead -minIdentity=90 -minScore=65 "
        blat_vr_pair_2 += Vector_Contaminants + " "
        blat_vr_pair_2 += os.path.join(vector_removal_folder, "pair_2_no_vectors.fasta")
        blat_vr_pair_2 += " -fine -q=rna -t=dna -out=blast8 -threads=" + self.Threads_str + " "
        blat_vr_pair_2 += os.path.join(vector_removal_folder, "pair_2_no_vectors.blatout")

        blat_containment_vector_singletons = ">&2 echo BLAT contaminant singletons | "
        blat_containment_vector_singletons += self.tool_path_obj.Python + " " + self.tool_path_obj.BLAT_Contaminant_Filter + " "
        blat_containment_vector_singletons += os.path.join(vector_removal_folder,
                                                           "singletons_no_vectors.fastq") + " "  # in
        blat_containment_vector_singletons += os.path.join(vector_removal_folder,
                                                           "singletons_no_vectors.blatout") + " "  # in
        blat_containment_vector_singletons += os.path.join(blat_containment_vector_folder,
                                                           "singletons_no_vectors.fastq") + " "  # out
        blat_containment_vector_singletons += os.path.join(blat_containment_vector_folder,
                                                           "singletons_vectors_only.fastq")  # out

        blat_containment_vector_pair_1 = ">&2 echo BLAT contaminant pair 1 | "
        blat_containment_vector_pair_1 += self.tool_path_obj.Python + " " + self.tool_path_obj.BLAT_Contaminant_Filter + " "
        blat_containment_vector_pair_1 += os.path.join(vector_removal_folder, "pair_1_no_vectors.fastq") + " "
        blat_containment_vector_pair_1 += os.path.join(vector_removal_folder, "pair_1_no_vectors.blatout") + " "
        blat_containment_vector_pair_1 += os.path.join(blat_containment_vector_folder, "pair_1_no_vectors.fastq") + " "
        blat_containment_vector_pair_1 += os.path.join(blat_containment_vector_folder, "pair_1_vectors_only.fastq")

        blat_containment_vector_pair_2 = ">&2 echo BLAT contaminant pair 2 | "
        blat_containment_vector_pair_2 += self.tool_path_obj.Python + " " + self.tool_path_obj.BLAT_Contaminant_Filter + " "
        blat_containment_vector_pair_2 += os.path.join(vector_removal_folder, "pair_2_no_vectors.fastq") + " "
        blat_containment_vector_pair_2 += os.path.join(vector_removal_folder, "pair_2_no_vectors.blatout") + " "
        blat_containment_vector_pair_2 += os.path.join(blat_containment_vector_folder, "pair_2_no_vectors.fastq") + " "
        blat_containment_vector_pair_2 += os.path.join(blat_containment_vector_folder, "pair_2_vectors_only.fastq")

        copy_singletons = "cp " + os.path.join(blat_containment_vector_folder, "singletons_no_vectors.fastq") + " "
        copy_singletons += os.path.join(final_folder, "singletons.fastq")

        copy_pair_1 = "cp " + os.path.join(blat_containment_vector_folder, "pair_1_no_vectors.fastq") + " "
        copy_pair_1 += os.path.join(final_folder, "pair_1.fastq")

        copy_pair_2 = "cp " + os.path.join(blat_containment_vector_folder, "pair_2_no_vectors.fastq") + " "
        copy_pair_2 += os.path.join(final_folder, "pair_2.fastq")
        
        data_change_vectors = ">&2 echo checking changes from host filter to vector filter | "
        data_change_vectors += self.tool_path_obj.Python + " "
        data_change_vectors += self.tool_path_obj.data_change_metrics + " "
        if(self.read_mode == "single"):
            data_change_vectors += os.path.join(dependency_folder, "singletons.fastq") + " "
            data_change_vectors += os.path.join(final_folder, "singletons.fastq") + " "
            data_change_vectors += os.path.join(final_folder, "host_to_vectors_singletons.tsv")
        elif(self.read_mode == "paired"):
            data_change_vectors += os.path.join(dependency_folder, "pair_1.fastq") + " "
            data_change_vectors += os.path.join(final_folder, "pair_1.fastq") + " "
            data_change_vectors += os.path.join(final_folder, "host_to_vectors_pair_1.tsv")

        if self.read_mode == "single":
            COMMANDS_vector = [
                copy_vector,
                bwa_vr_prep,
                samtools_vr_prep,
                bwa_vr_singletons,
                samtools_no_vector_singletons_sam_to_bam,
                samtools_no_vector_singletons_bam_to_fastq,
                samtools_vector_singletons_bam_to_fastq,
                make_blast_db_vector,
                vsearch_filter_6,
                blat_vr_singletons,
                blat_containment_vector_singletons,
                copy_singletons,
                data_change_vectors
            ]
        elif self.read_mode == "paired":
            COMMANDS_vector = [
                copy_vector,
                bwa_vr_prep,
                samtools_vr_prep,
                bwa_vr_singletons,
                samtools_no_vector_singletons_sam_to_bam,
                samtools_no_vector_singletons_bam_to_fastq,
                samtools_vector_singletons_bam_to_fastq,
                bwa_vr_pair_1,
                bwa_vr_pair_2,
                samtools_vr_pair_1_sam_to_bam,
                samtools_no_vector_pair_1_bam_to_fastq,
                samtools_vector_pair_1_bam_to_fastq,
                samtools_vr_pair_2_sam_to_bam,
                samtools_no_vector_pair_2_bam_to_fastq,
                samtools_vector_pair_2_bam_to_fastq,
                make_blast_db_vector,
                vsearch_filter_6,
                vsearch_filter_7,
                vsearch_filter_8,
                blat_vr_singletons,
                blat_vr_pair_1,
                blat_vr_pair_2,
                blat_containment_vector_singletons,
                blat_containment_vector_pair_1,
                blat_containment_vector_pair_2,
                copy_singletons,
                copy_pair_1,
                copy_pair_2,
                data_change_vectors
            ]

        return COMMANDS_vector

    #oct 31, 2019: dep'd function.  we now split on constant chunksize, not constant chunks
    # def create_rRNA_filter_prep_command(self, stage_name, file_split_count, dependency_name, operating_mode = "single"):
        # # split data into mRNA and rRNA so we can focus on the mRNA for the remainder of the analysis steps
        # dep_loc                 = os.path.join(self.Output_Path, dependency_name, "final_results")
        # subfolder               = os.path.join(self.Output_Path, stage_name)
        # data_folder             = os.path.join(subfolder, "data")
        # singleton_split_folder  = os.path.join(data_folder, "singletons", "singletons_fastq")
        
        # self.make_folder(subfolder)
        # self.make_folder(data_folder)
        # self.make_folder(singleton_split_folder)
                
        # file_splitter_singletons = self.tool_path_obj.Python + " " + self.tool_path_obj.File_splitter + " "
        # file_splitter_singletons += os.path.join(dep_loc, "singletons.fastq") + " "
        # file_splitter_singletons += os.path.join(singleton_split_folder, "singletons") + " "
        # file_splitter_singletons += str(file_split_count)
        
        # file_splitter_pair_1 = None
        # file_splitter_pair_2 = None
        
        # if(operating_mode == "paired"):
            # pair_1_split_folder     = os.path.join(data_folder, "pair_1", "pair_1_fastq")
            # pair_2_split_folder     = os.path.join(data_folder, "pair_2", "pair_2_fastq")
            # self.make_folder(pair_1_split_folder)
            # self.make_folder(pair_2_split_folder)        

            # file_splitter_pair_1 = self.tool_path_obj.Python + " " + self.tool_path_obj.File_splitter + " "
            # file_splitter_pair_1 += os.path.join(dep_loc, "pair_1.fastq") + " "
            # file_splitter_pair_1 += os.path.join(pair_1_split_folder, "pair_1") + " "
            # file_splitter_pair_1 += str(file_split_count)

            # file_splitter_pair_2 = self.tool_path_obj.Python + " " + self.tool_path_obj.File_splitter + " "
            # file_splitter_pair_2 += os.path.join(dep_loc, "pair_2.fastq") + " "
            # file_splitter_pair_2 += os.path.join(pair_2_split_folder, "pair_2") + " "
            # file_splitter_pair_2 += str(file_split_count)
            
        # if self.read_mode == "single":
            # COMMANDS_rRNA_prep = [
                # file_splitter_singletons
            # ]
        # elif self.read_mode == "paired":
            # COMMANDS_rRNA_prep = [
                # file_splitter_singletons,
                # file_splitter_pair_1,
                # file_splitter_pair_2
            # ]
        # #print(dt.today(), COMMANDS_rRNA_prep)
        # return COMMANDS_rRNA_prep
        
    def create_rRNA_filter_prep_command_2nd_split(self, stage_name, category, file_to_split, split_count):
        #this splits a file into separate-but-equal portions 
        #dep_loc                 = os.path.join(self.Output_Path, dependency_name, "final_results")
        subfolder               = os.path.join(self.Output_Path, stage_name)
        data_folder             = os.path.join(subfolder, "data")
        second_split_folder     = os.path.join(data_folder, category, category + "_second_split_fastq")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(second_split_folder)
        
        #remove_other_file = ">&2 echo removing previous split | "
        #remove_other_file += "rm" + " "
        #remove_other_file += split_folder + "*"
        
        
        base_name = os.path.basename(file_to_split)
        real_base = os.path.splitext(base_name)[0]
        second_output_path = os.path.join(second_split_folder, real_base)
        #this operates on fastq.  Jul 8, 2020: fastq split now done on constant chunksize
        split_data = ">&2 echo splitting data into chunks: " + category + " | "
        split_data += self.tool_path_obj.Python + " "
        split_data += self.tool_path_obj.File_splitter + " "
        split_data += file_to_split + " "
        #split_data += file_to_split.split(".")[0] + " "
        split_data += second_output_path + " "
        split_data += str(split_count)
        
        print("-----------------")
        print(dt.today(), file_to_split)
        print(dt.today(), file_to_split.split(".")[0])
        print(dt.today(), "output path FROM COMMANDS second split:", second_output_path)
        COMMANDS_2nd_split = [
            split_data
        ]
        
        return COMMANDS_2nd_split
        
        
        
    def create_rRNA_filter_prep_command_v3(self, stage_name, category, dependency_name, chunks):
        #split the data into tiny shards.  called once
        dep_loc                 = os.path.join(self.Output_Path, dependency_name, "final_results")
        subfolder               = os.path.join(self.Output_Path, stage_name)
        data_folder             = os.path.join(subfolder, "data")
        split_folder            = os.path.join(data_folder, category + "_fastq")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(split_folder)
        
        split_fastq = ">&2 echo splitting fastq for " + category + " | " 
        split_fastq += self.tool_path_obj.Python + " "
        split_fastq += self.tool_path_obj.File_splitter + " "
        split_fastq += os.path.join(dep_loc, category + ".fastq") + " "
        split_fastq += os.path.join(split_folder, category) + " "
        split_fastq += self.rRNA_chunks
        
        return [split_fastq]

    def create_rRNA_filter_convert_fastq_command(self, stage_name, category, fastq_name):
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        jobs_folder         = os.path.join(data_folder, "jobs")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_folder         = os.path.join(data_folder, category + "_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_rRNA")
        file_name           = fastq_name.split(".")[0]
        
        fastq_seqs          = os.path.join(fastq_folder, fastq_name)
        
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)
        self.make_folder(infernal_out_folder)
        self.make_folder(mRNA_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(jobs_folder)
        
        convert_fastq_to_fasta = ">&2 echo " + " converting " + file_name + " file to fasta | "
        convert_fastq_to_fasta += self.tool_path_obj.vsearch
        convert_fastq_to_fasta += " --fastq_filter " + fastq_seqs
        convert_fastq_to_fasta += " --fastq_ascii " + self.Qual_str
        convert_fastq_to_fasta += " --fastaout " + fasta_seqs
        
        return [convert_fastq_to_fasta]
    
    def create_rRNA_filter_barrnap_arc_command(self, stage_name, category, fastq_name):
        # called by each split file
        # category -> singletons, pair 1, pair 2
        # file name -> the specific split section of the category (the fastq segments)
        # stage_name -> "rRNA_Filter"
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        jobs_folder         = os.path.join(data_folder, "jobs")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_folder         = os.path.join(data_folder, category + "_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_rRNA")
        file_name           = fastq_name.split(".")[0]
        Barrnap_arc_out     = os.path.join(Barrnap_out_folder, file_name + "_arc.barrnap_out")
        Barrnap_bac_out     = os.path.join(Barrnap_out_folder, file_name + "_bac.barrnap_out")
        Barrnap_euk_out     = os.path.join(Barrnap_out_folder, file_name + "_euk.barrnap_out")
        Barrnap_mit_out     = os.path.join(Barrnap_out_folder, file_name + "_mit.barrnap_out")
        infernal_out        = os.path.join(infernal_out_folder, file_name + ".infernal_out")
        
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)
        self.make_folder(infernal_out_folder)
        self.make_folder(mRNA_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(jobs_folder)
     
        Barrnap_archaea = ">&2 echo running Barrnap on " + file_name + " file: arc | "
        Barrnap_archaea += self.tool_path_obj.Barrnap
        Barrnap_archaea += " --quiet --reject 0.01 --kingdom " + "arc"
        Barrnap_archaea += " --threads " + self.Threads_str
        Barrnap_archaea += " " + fasta_seqs
        Barrnap_archaea += " >> " + Barrnap_arc_out

  
        return [Barrnap_archaea]
         
        
    def create_rRNA_filter_barrnap_bac_command(self, stage_name, category, fastq_name):

        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        file_name           = fastq_name.split(".")[0]
        Barrnap_bac_out     = os.path.join(Barrnap_out_folder, file_name + "_bac.barrnap_out")
        
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)

        Barrnap_bacteria = ">&2 echo Running Barrnap on " + file_name + " file:  bac | "
        Barrnap_bacteria += self.tool_path_obj.Barrnap
        Barrnap_bacteria += " --quiet --reject 0.01 --kingdom " + "bac"
        Barrnap_bacteria += " --threads " + self.Threads_str
        Barrnap_bacteria += " " + fasta_seqs
        Barrnap_bacteria += " >> " + Barrnap_bac_out

        return [Barrnap_bacteria]
        
    def create_rRNA_filter_barrnap_euk_command(self, stage_name, category, fastq_name):

        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        file_name           = fastq_name.split(".")[0]
        Barrnap_euk_out     = os.path.join(Barrnap_out_folder, file_name + "_euk.barrnap_out")
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)

        Barrnap_eukaryote = ">&2 echo Running Barrnap on " + file_name + " file: euk | "
        Barrnap_eukaryote += self.tool_path_obj.Barrnap
        Barrnap_eukaryote += " --quiet --reject 0.01 --kingdom " + "euk"
        Barrnap_eukaryote += " --threads " + self.Threads_str
        Barrnap_eukaryote += " " + fasta_seqs
        Barrnap_eukaryote += " >> " + Barrnap_euk_out

        return [Barrnap_eukaryote]
        
    def create_rRNA_filter_barrnap_mit_command(self, stage_name, category, fastq_name):
        #designed to run on a single split sample.
        #expected to be merged later with all the other runs of the same fastq name
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        file_name           = fastq_name.split(".")[0]
        Barrnap_mit_out     = os.path.join(Barrnap_out_folder, file_name + "_mit.barrnap_out")
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)

        Barrnap_mitochondria = ">&2 echo Running Barrnap on " + file_name + " file: mito | " 
        Barrnap_mitochondria += self.tool_path_obj.Barrnap
        Barrnap_mitochondria += " --quiet --reject 0.01 --kingdom " + "mito"
        Barrnap_mitochondria += " --threads " + self.Threads_str
        Barrnap_mitochondria += " " + fasta_seqs
        Barrnap_mitochondria += " >> " + Barrnap_mit_out

        return [Barrnap_mitochondria]
        
        
        
        
        
        
    def create_rRNA_filter_barrnap_cat_command(self, stage_name, category, fastq_name):
        #this is expected to run on each sample split
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        jobs_folder         = os.path.join(data_folder, "jobs")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_folder         = os.path.join(data_folder, category + "_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_rRNA")
        file_name           = fastq_name.split(".")[0]
        Barrnap_arc_out     = os.path.join(Barrnap_out_folder, file_name + "_arc.barrnap_out")
        Barrnap_bac_out     = os.path.join(Barrnap_out_folder, file_name + "_bac.barrnap_out")
        Barrnap_euk_out     = os.path.join(Barrnap_out_folder, file_name + "_euk.barrnap_out")
        Barrnap_mit_out     = os.path.join(Barrnap_out_folder, file_name + "_mit.barrnap_out")
        infernal_out        = os.path.join(infernal_out_folder, file_name + ".infernal_out")
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")
        Barrnap_out         = os.path.join(Barrnap_out_folder, file_name + ".barrnap_out")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)
        self.make_folder(infernal_out_folder)
        self.make_folder(mRNA_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(jobs_folder)
        
        #combine the arc, bac, euk, mit files into 1
        cat_command = ">&2 echo Combining files for:" + file_name + " | "
        cat_command += "cat" + " "
        cat_command += Barrnap_arc_out + " " + Barrnap_bac_out + " " + Barrnap_euk_out + " " + Barrnap_mit_out + " "
        cat_command += ">>" + " " + Barrnap_out
        
        rm_arc = ">&2 echo delete arc: " + file_name + " | "
        rm_arc += "rm" + " "
        rm_arc += Barrnap_arc_out
        
        rm_bac = ">&2 echo delete bac: " + file_name + " | "
        rm_bac += "rm" + " "
        rm_bac += Barrnap_bac_out
        
        rm_euk = ">&2 echo delete euk: " + file_name + " | "
        rm_euk += "rm" + " "
        rm_euk += Barrnap_euk_out
        
        rm_mit = ">&2 echo delete mit: " + file_name + " | "
        rm_mit += "rm" + " "
        rm_mit += Barrnap_mit_out
        
        return [cat_command, rm_arc, rm_bac, rm_euk, rm_mit]
        
        
    def create_rRNA_filter_barrnap_pp_command(self, stage_name, category, fastq_name):
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        jobs_folder         = os.path.join(data_folder, "jobs")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_folder         = os.path.join(data_folder, category + "_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_rRNA")
        file_name           = fastq_name.split(".")[0]
        Barrnap_out         = os.path.join(Barrnap_out_folder, file_name + ".barrnap_out")
        
        fastq_seqs          = os.path.join(fastq_folder, fastq_name)
        
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(fasta_folder)
        self.make_folder(Barrnap_out_folder)
        self.make_folder(infernal_out_folder)
        self.make_folder(mRNA_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(jobs_folder)
        
        
        Barrnap_pp = ">&2 echo Running Barrnap pp scripts | "
        Barrnap_pp += self.tool_path_obj.Python + " "
        Barrnap_pp += self.tool_path_obj.barrnap_post + " "
        Barrnap_pp += Barrnap_out + " "
        Barrnap_pp += fastq_seqs + " "
        Barrnap_pp += mRNA_folder + " "
        Barrnap_pp += rRNA_folder + " "
        Barrnap_pp += file_name + "_barrnap"
        
        make_marker = ">&2 echo " + file_name + "_barrnap Marking job completed | " 
        make_marker += "touch" + " " 
        make_marker += os.path.join(jobs_folder, file_name + "_barrnap")
        
        return [Barrnap_pp + " && " + make_marker]
        
        
    def create_rRNA_filter_infernal_prep_command(self, stage_name, category, fastq_name):
        #expecting full file name in fastq_name
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap_mRNA_fasta")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_folder         = os.path.join(data_folder, category + "_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_rRNA")
        file_name           = fastq_name.split(".")[0]
        Barrnap_out         = os.path.join(Barrnap_out_folder, file_name + ".barrnap_out")
        infernal_out        = os.path.join(infernal_out_folder, file_name + ".infernal_out")
        
        fastq_seqs          = os.path.join(fastq_folder, fastq_name)
        
        fasta_seqs          = os.path.join(fasta_folder, file_name + ".fasta")

        self.make_folder(infernal_out_folder)
        self.make_folder(mRNA_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(Barrnap_out_folder)
        
        convert_fastq_to_fasta_barrnap = ">&2 echo converting barrnap fastq to fasta:" + file_name + " | "
        convert_fastq_to_fasta_barrnap += self.tool_path_obj.vsearch
        convert_fastq_to_fasta_barrnap += " --fastq_filter " + os.path.join(mRNA_folder, fastq_name)
        convert_fastq_to_fasta_barrnap += " --fastq_ascii " + self.Qual_str
        convert_fastq_to_fasta_barrnap += " --fastaout " + os.path.join(Barrnap_out_folder, file_name + ".fasta")
        
        return [convert_fastq_to_fasta_barrnap]

    def create_rRNA_filter_infernal_command(self, stage_name, category, file_name):
    
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap_mRNA_fasta")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_folder         = os.path.join(data_folder, category + "_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_rRNA")
        Barrnap_out         = os.path.join(Barrnap_out_folder, file_name + ".barrnap_out")
        infernal_out        = os.path.join(infernal_out_folder, file_name + ".infernal_out")
        jobs_folder         = os.path.join(data_folder, "jobs")

        self.make_folder(infernal_out_folder)
        self.make_folder(mRNA_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(Barrnap_out_folder)
        self.make_folder(jobs_folder)
        

        infernal_command = ">&2 echo " + str(dt.today()) + " running infernal on " + file_name + " file | "
        infernal_command += self.tool_path_obj.Infernal
        infernal_command += " -o /dev/null --tblout "
        infernal_command += infernal_out
        #infernal_command += " --cpu " + self.Threads_str -> lined nerf'd because infernal's parallelism is not good
        infernal_command += " --cpu 1"
        infernal_command += " --anytrunc --rfam -E 0.001 "
        infernal_command += self.tool_path_obj.Rfam + " "
        infernal_command += os.path.join(Barrnap_out_folder, file_name + "_barrnap_mRNA.fasta")

        make_marker = ">&2 echo " + file_name + "_infernal Marking job completed | " 
        make_marker += "touch" + " " 
        make_marker += os.path.join(jobs_folder, file_name + "_infernal")
        
        COMMANDS_infernal = [infernal_command + " && " + make_marker]
        return COMMANDS_infernal

    def create_rRNA_filter_splitter_command(self, stage_name, category, file_name):
    
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        fasta_folder        = os.path.join(data_folder, category + "_fasta")
        fastq_folder        = os.path.join(data_folder, category + "_fastq")
        Barrnap_out_folder  = os.path.join(data_folder, category + "_barrnap_mRNA_fasta")
        infernal_out_folder = os.path.join(data_folder, category + "_infernal")
        mRNA_barrnap_folder = os.path.join(data_folder, category + "_mRNA")
        mRNA_infernal_folder= os.path.join(data_folder, category + "_infernal_mRNA")
        rRNA_folder         = os.path.join(data_folder, category + "_infernal_rRNA")
        infernal_out        = os.path.join(infernal_out_folder, file_name + ".infernal_out")
        
        self.make_folder(mRNA_infernal_folder)
        self.make_folder(rRNA_folder)
        
        rRNA_filtration = ">&2 echo " + str(dt.today()) + " Getting the actual reads out of Infernal: " + file_name + " | "
        rRNA_filtration += self.tool_path_obj.Python + " "
        rRNA_filtration += self.tool_path_obj.rRNA_filter + " "
        rRNA_filtration += infernal_out + " "
        rRNA_filtration += os.path.join(mRNA_barrnap_folder, file_name + "_barrnap_mRNA.fastq") + " "
        rRNA_filtration += mRNA_infernal_folder + " "
        rRNA_filtration += rRNA_folder + " "
        rRNA_filtration += file_name + "_infernal"
        
        return [rRNA_filtration]

    def create_rRNA_filter_post_command(self, dependency_stage_name, stage_name):
        # rRNA filtration orphaned some reads in the pairs.  We need to refilter the singletons.
        # Cat then refilter
        dep_folder                  = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        subfolder                   = os.path.join(self.Output_Path, stage_name)
        data_folder                 = os.path.join(subfolder, "data")
        pre_filter_folder           = os.path.join(data_folder, "0_pre_singletons")
        pre_filter_mRNA_folder      = os.path.join(pre_filter_folder, "mRNA")
        pre_filter_rRNA_folder      = os.path.join(pre_filter_folder, "rRNA")
        singletons_mRNA_folder      = os.path.join(data_folder, "singletons_mRNA")
        singletons_rRNA_folder      = os.path.join(data_folder, "singletons_rRNA")
        pair_1_mRNA_folder          = os.path.join(data_folder, "pair_1_mRNA")
        pair_1_barrnap_mRNA_folder  = 
        pair_1_rRNA_folder          = os.path.join(data_folder, "pair_1_rRNA")
        pair_2_mRNA_folder          = os.path.join(data_folder, "pair_2_mRNA")
        pair_2_rRNA_folder          = os.path.join(data_folder, "pair_2_rRNA")
        final_folder                = os.path.join(subfolder, "final_results")
        final_mRNA_folder           = os.path.join(final_folder, "mRNA")
        final_rRNA_folder           = os.path.join(final_folder, "rRNA")

        self.make_folder(pre_filter_folder)
        self.make_folder(pre_filter_mRNA_folder)
        self.make_folder(pre_filter_rRNA_folder)
        self.make_folder(final_folder)
        self.make_folder(final_mRNA_folder)
        self.make_folder(final_rRNA_folder)

        if self.read_mode == "single":
            cat_singletons_mRNA = "for f in" + " "
            cat_singletons_mRNA += singletons_mRNA_folder 
            cat_singletons_mRNA += "/*; do cat \"$f\" >>" + " " 
            cat_singletons_mRNA += os.path.join(final_mRNA_folder, "singletons.fastq") 
            cat_singletons_mRNA += "; done"
            
            
            #cat_singletons_rRNA = "cat " + singletons_rRNA_folder + "/* 1>>" + os.path.join(final_rRNA_folder, "singletons.fastq")
            cat_singletons_rRNA = "for f in" + " "
            cat_singletons_rRNA += singletons_rRNA_folder
            cat_singletons_rRNA += "/*; do cat \"$f\" >>" + " "
            cat_singletons_rRNA += os.path.join(final_rRNA_folder, "singletons.fastq")
            cat_singletons_rRNA += "; done"
            
            
        elif self.read_mode == "paired":
            #cat_singletons_mRNA = "cat " + singletons_mRNA_folder + "/* 1>>" + os.path.join(pre_filter_mRNA_folder, "singletons.fastq")
            #cat_singletons_rRNA = "cat " + singletons_rRNA_folder + "/* 1>>" + os.path.join(pre_filter_rRNA_folder, "singletons.fastq")
            cat_singletons_mRNA = "for f in" + " "
            cat_singletons_mRNA += singletons_mRNA_folder
            cat_singletons_mRNA += "/*; do cat \"$f\" >>" + " "
            cat_singletons_mRNA += os.path.join(pre_filter_mRNA_folder, "singletons.fastq")
            cat_singletons_mRNA += "; done"
            
            cat_singletons_rRNA = "for f in" + " "
            cat_singletons_rRNA += singletons_rRNA_folder
            cat_singletons_rRNA += "/*; do cat \"$f\" >>" + " "
            cat_singletons_rRNA += os.path.join(pre_filter_rRNA_folder, "singletons.fastq")
            cat_singletons_rRNA += "; done"
            
            

        #cat_pair_1_mRNA = "cat " + pair_1_mRNA_folder + "/* 1>>" + os.path.join(pre_filter_mRNA_folder, "pair_1.fastq")
        #cat_pair_1_rRNA = "cat " + pair_1_rRNA_folder + "/* 1>>" + os.path.join(pre_filter_rRNA_folder, "pair_1.fastq")
        cat_pair_1_mRNA = "for f in" + " "
        cat_pair_1_mRNA += pair_1_mRNA_folder 
        cat_pair_1_mRNA += "/*; do cat \"$f\" >>" + " "
        cat_pair_1_mRNA += os.path.join(pre_filter_mRNA_folder, "pair_1.fastq")
        cat_pair_1_mRNA += "; done"
        
        cat_pair_1_rRNA = "for f in" + " "
        cat_pair_1_rRNA += pair_1_rRNA_folder 
        cat_pair_1_rRNA += "/*; do cat \"$f\" >>" + " "
        cat_pair_1_rRNA += os.path.join(pre_filter_rRNA_folder, "pair_1.fastq")
        cat_pair_1_rRNA += "; done"
        
        #cat_pair_2_mRNA = "cat " + pair_2_mRNA_folder + "/* 1>>" + os.path.join(pre_filter_mRNA_folder, "pair_2.fastq")
        #cat_pair_2_rRNA = "cat " + pair_2_rRNA_folder + "/* 1>>" + os.path.join(pre_filter_rRNA_folder, "pair_2.fastq")

        cat_pair_2_mRNA = "for f in" + " "
        cat_pair_2_mRNA += pair_2_mRNA_folder 
        cat_pair_2_mRNA += "/*; do cat \"$f\" >>" + " "
        cat_pair_2_mRNA += os.path.join(pre_filter_mRNA_folder, "pair_2.fastq")
        cat_pair_2_mRNA += "; done"
        
        cat_pair_2_rRNA = "for f in" + " "
        cat_pair_2_rRNA += pair_2_rRNA_folder 
        cat_pair_2_rRNA += "/*; do cat \"$f\" >>" + " "
        cat_pair_2_rRNA += os.path.join(pre_filter_rRNA_folder, "pair_2.fastq")
        cat_pair_2_rRNA += "; done"
        
        


        singleton_mRNA_filter = ">&2 echo " + str(dt.today()) + " filtering mRNA for singletons | "
        singleton_mRNA_filter += self.tool_path_obj.Python + " "
        singleton_mRNA_filter += self.tool_path_obj.orphaned_read_filter + " "
        singleton_mRNA_filter += os.path.join(pre_filter_mRNA_folder, "pair_1.fastq") + " "
        singleton_mRNA_filter += os.path.join(pre_filter_mRNA_folder, "pair_2.fastq") + " "
        singleton_mRNA_filter += os.path.join(pre_filter_mRNA_folder, "singletons.fastq") + " "
        singleton_mRNA_filter += os.path.join(final_mRNA_folder, "pair_1.fastq") + " "
        singleton_mRNA_filter += os.path.join(final_mRNA_folder, "pair_2.fastq") + " "
        singleton_mRNA_filter += os.path.join(final_mRNA_folder, "singletons.fastq")

        singleton_rRNA_filter = ">&2 echo " + str(dt.today()) + " filtering rRNA for singletons | "
        singleton_rRNA_filter += self.tool_path_obj.Python + " "
        singleton_rRNA_filter += self.tool_path_obj.orphaned_read_filter + " "
        singleton_rRNA_filter += os.path.join(pre_filter_rRNA_folder, "pair_1.fastq") + " "
        singleton_rRNA_filter += os.path.join(pre_filter_rRNA_folder, "pair_2.fastq") + " "
        singleton_rRNA_filter += os.path.join(pre_filter_rRNA_folder, "singletons.fastq") + " "
        singleton_rRNA_filter += os.path.join(final_rRNA_folder, "pair_1.fastq") + " "
        singleton_rRNA_filter += os.path.join(final_rRNA_folder, "pair_2.fastq") + " "
        singleton_rRNA_filter += os.path.join(final_rRNA_folder, "singletons.fastq")
        
        # data_change_rRNA = ">&2 echo scanning for relative change between vector filter and rRNA removal rRNA | "
        # data_change_rRNA += self.tool_path_obj.Python + " "
        # data_change_rRNA += self.tool_path_obj.data_change_metrics + " "
        # if(self.read_mode == "single"):
            # data_change_rRNA += os.path.join(dep_folder, "singletons.fastq") + " "
            # data_change_rRNA += os.path.join(final_rRNA_folder, "singletons.fastq") + " "
            # data_change_rRNA += os.path.join(final_folder, "vector_to_rRNA_singletons.tsv")
        # elif(self.read_mode == "paired"):
            # data_change_rRNA += os.path.join(dep_folder, "pair_1.fastq") + " "
            # data_change_rRNA += os.path.join(final_rRNA_folder, "pair_1.fastq") + " "
            # data_change_rRNA += os.path.join(final_folder, "vector_to_rRNA_pair_1.tsv")
        
        # data_change_mRNA = ">&2 echo scanning for relative change between vector filter and rRNA removal mRNA | "
        # data_change_mRNA += self.tool_path_obj.Python + " "
        # data_change_mRNA += self.tool_path_obj.data_change_metrics + " "
        # if(self.read_mode == "single"):
            # data_change_mRNA += os.path.join(dep_folder, "singletons.fastq") + " "
            # data_change_mRNA += os.path.join(final_mRNA_folder, "singletons.fastq") + " "
            # data_change_mRNA += os.path.join(final_folder, "vector_to_mRNA_singletons.tsv")
        # elif(self.read_mode == "paired"):
            # data_change_mRNA += os.path.join(dep_folder, "pair_1.fastq") + " "
            # data_change_mRNA += os.path.join(final_mRNA_folder, "pair_1.fastq") + " "
            # data_change_mRNA += os.path.join(final_folder, "vector_to_mRNA_pair_1.tsv")
        
        if self.read_mode == "single":
            COMMANDS_rRNA_post = [
                cat_singletons_mRNA,
                cat_singletons_rRNA#,
                #data_change_mRNA,
                #data_change_rRNA
            ]
        elif self.read_mode == "paired":
            COMMANDS_rRNA_post = [
                cat_singletons_mRNA,
                cat_singletons_rRNA,
                cat_pair_1_mRNA,
                cat_pair_1_rRNA,
                cat_pair_2_mRNA,
                cat_pair_2_rRNA,
                singleton_mRNA_filter,
                singleton_rRNA_filter#,
                #data_change_mRNA,
                #data_change_rRNA
            ]

        return COMMANDS_rRNA_post

    def create_repop_command(self, stage_name, preprocess_stage_name, dependency_stage_name):
        # This stage reintroduces the duplicate reads into the data.  We need it to count towards things.
        # Due to time, and hierarchical importance, we're leaving this stage alone.
        # Leaving it alone in a tangled state
        # But the issue is that by leaving it alone, we violate the design plan
        # The fix? We have to detect if preprocess has been run.  If so, pull the missing data there
        # if not,
        # What has to happen here:
        # -> detect if we've run the preprocess stage.
        # -> if it's run, grab data
        # -> if not, run our own custom preprocess up to what we need
        dep_loc                 = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        subfolder               = os.path.join(self.Output_Path, stage_name)
        data_folder             = os.path.join(subfolder, "data")
        repop_folder            = os.path.join(data_folder, "0_repop")
        final_folder            = os.path.join(subfolder, "final_results")
        preprocess_subfolder    = os.path.join(self.Output_Path, preprocess_stage_name)

        # we ran a previous preprocess.  grab files
        # need 3, 5(clstr only), and mRNA from the 2nd stage.
        hq_path                 = os.path.join(preprocess_subfolder, "final_results")
        cluster_path            = os.path.join(preprocess_subfolder, "final_results")
        singleton_path          = os.path.join(preprocess_subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(repop_folder)
        self.make_folder(final_folder)

        repop_singletons = ">&2 echo " + str(dt.today()) + " Duplication repopulation singletons mRNA| "
        repop_singletons += self.tool_path_obj.Python + " " + self.tool_path_obj.duplicate_repopulate + " "
        if self.read_mode == "single":
            repop_singletons += os.path.join(singleton_path, "singletons_hq.fastq") + " "
        elif self.read_mode == "paired":
            repop_singletons += os.path.join(hq_path, "singletons_with_duplicates.fastq") + " "
        repop_singletons += os.path.join(dep_loc, "mRNA", "singletons.fastq") + " "  # in -> rRNA filtration output
        repop_singletons += os.path.join(cluster_path, "singletons_unique.fastq.clstr") + " "  # in -> duplicates filter output
        if self.read_mode == "single":
            repop_singletons += os.path.join(final_folder, "singletons.fastq")  # out
        elif self.read_mode == "paired":
            repop_singletons += os.path.join(repop_folder, "singletons.fastq")  # out

        repop_singletons_rRNA = ">&2 echo " + str(dt.today()) + " Duplication repopulations singletons rRNA | "
        repop_singletons_rRNA += self.tool_path_obj.Python + " " + self.tool_path_obj.duplicate_repopulate + " "
        if self.read_mode == "single":
            repop_singletons_rRNA += os.path.join(singleton_path, "singletons_hq.fastq") + " "
        elif self.read_mode == "paired":
            repop_singletons_rRNA += os.path.join(hq_path, "singletons_with_duplicates.fastq") + " "
        repop_singletons_rRNA += os.path.join(dep_loc, "rRNA", "singletons.fastq") + " "  # in -> rRNA filtration output
        repop_singletons_rRNA += os.path.join(cluster_path, "singletons_unique.fastq.clstr") + " "  # in -> duplicates filter output
        if self.read_mode == "single":
            repop_singletons_rRNA += os.path.join(final_folder, "singletons_rRNA.fastq")  # out
        elif self.read_mode == "paired":
            repop_singletons_rRNA += os.path.join(repop_folder, "singletons_rRNA.fastq")  # out

        repop_pair_1 = ">&2 echo " + str(dt.today()) + " Duplication repopulation pair 1 mRNA | "
        repop_pair_1 += self.tool_path_obj.Python + " " + self.tool_path_obj.duplicate_repopulate + " "
        repop_pair_1 += os.path.join(hq_path, "pair_1_match.fastq") + " "
        repop_pair_1 += os.path.join(dep_loc, "mRNA", "pair_1.fastq") + " "
        repop_pair_1 += os.path.join(cluster_path, "pair_1_unique.fastq.clstr") + " "
        repop_pair_1 += os.path.join(repop_folder, "pair_1.fastq")

        repop_pair_1_rRNA = ">&2 echo " + str(dt.today()) + " Duplication repopulation pair 1 rRNA | "
        repop_pair_1_rRNA += self.tool_path_obj.Python + " " + self.tool_path_obj.duplicate_repopulate + " "
        repop_pair_1_rRNA += os.path.join(hq_path, "pair_1_match.fastq") + " "
        repop_pair_1_rRNA += os.path.join(dep_loc, "rRNA", "pair_1.fastq") + " "
        repop_pair_1_rRNA += os.path.join(cluster_path, "pair_1_unique.fastq.clstr") + " "
        repop_pair_1_rRNA += os.path.join(repop_folder, "pair_1_rRNA.fastq")

        repop_pair_2 = ">&2 echo " + str(dt.today()) + " Duplication repopulation pair 2 | "
        repop_pair_2 += self.tool_path_obj.Python + " " + self.tool_path_obj.duplicate_repopulate + " "
        repop_pair_2 += os.path.join(hq_path, "pair_2_match.fastq") + " "
        repop_pair_2 += os.path.join(dep_loc, "mRNA", "pair_2.fastq") + " "
        repop_pair_2 += os.path.join(cluster_path, "pair_2_unique.fastq.clstr") + " "
        repop_pair_2 += os.path.join(repop_folder, "pair_2.fastq")

        repop_pair_2_rRNA = ">&2 echo " + str(dt.today()) + " Duplication repopulation pair 2 | "
        repop_pair_2_rRNA = ">&2 echo " + str(dt.today()) + " Duplication repopulation pair 2 | "
        repop_pair_2_rRNA += self.tool_path_obj.Python + " " + self.tool_path_obj.duplicate_repopulate + " "
        repop_pair_2_rRNA += os.path.join(hq_path, "pair_2_match.fastq") + " "
        repop_pair_2_rRNA += os.path.join(dep_loc, "rRNA", "pair_2.fastq") + " "
        repop_pair_2_rRNA += os.path.join(cluster_path, "pair_2_unique.fastq.clstr") + " "
        repop_pair_2_rRNA += os.path.join(repop_folder, "pair_2_rRNA.fastq")

        singleton_repop_filter = ">&2 echo filtering mRNA for new singletons | "
        singleton_repop_filter += self.tool_path_obj.Python + " "
        singleton_repop_filter += self.tool_path_obj.orphaned_read_filter + " "
        singleton_repop_filter += os.path.join(repop_folder, "pair_1.fastq") + " "
        singleton_repop_filter += os.path.join(repop_folder, "pair_2.fastq") + " "
        singleton_repop_filter += os.path.join(repop_folder, "singletons.fastq") + " "
        singleton_repop_filter += os.path.join(final_folder, "pair_1.fastq") + " "
        singleton_repop_filter += os.path.join(final_folder, "pair_2.fastq") + " "
        singleton_repop_filter += os.path.join(final_folder, "singletons.fastq")
    
        singleton_repop_filter_rRNA = ">&2 echo filtering rRNA for new singletons | "  
        singleton_repop_filter_rRNA += self.tool_path_obj.Python + " "
        singleton_repop_filter_rRNA += self.tool_path_obj.orphaned_read_filter + " "
        singleton_repop_filter_rRNA += os.path.join(repop_folder, "pair_1_rRNA.fastq") + " "
        singleton_repop_filter_rRNA += os.path.join(repop_folder, "pair_2_rRNA.fastq") + " "
        singleton_repop_filter_rRNA += os.path.join(repop_folder, "singletons_rRNA.fastq") + " "
        singleton_repop_filter_rRNA += os.path.join(final_folder, "pair_1_rRNA.fastq") + " "
        singleton_repop_filter_rRNA += os.path.join(final_folder, "pair_2_rRNA.fastq") + " "
        singleton_repop_filter_rRNA += os.path.join(final_folder, "singletons_rRNA.fastq")
        
        data_change_repop_rRNA = ">&2 echo scanning for changes from rRNA filter to repop rRNA | "
        data_change_repop_rRNA += self.tool_path_obj.Python + " "
        data_change_repop_rRNA += self.tool_path_obj.data_change_metrics + " "
        if(self.read_mode == "single"):
            data_change_repop_rRNA += os.path.join(dep_loc, "singletons.fastq") + " "
            data_change_repop_rRNA += os.path.join(final_folder, "singletons_rRNA.fastq") + " "
            data_change_repop_rRNA += os.path.join(final_folder, "rRNA_filter_to_repop_rRNA_singletons.tsv")
        elif(self.read_mode == "paired"):
            data_change_repop_rRNA += os.path.join(dep_loc, "pair_1.fastq") + " "
            data_change_repop_rRNA += os.path.join(final_folder, "pair_1_rRNA.fastq") + " "
            data_change_repop_rRNA += os.path.join(final_folder, "rRNA_filter_to_repop_rRNA_pair_1.tsv")
            
        data_change_repop_mRNA = ">&2 echo scanning for changes from rRNA filter to repop mRNA | "
        data_change_repop_mRNA += self.tool_path_obj.Python + " "
        data_change_repop_mRNA += self.tool_path_obj.data_change_metrics + " "
        if(self.read_mode == "single"):
            data_change_repop_mRNA += os.path.join(dep_loc, "singletons.fastq") + " "
            data_change_repop_mRNA += os.path.join(final_folder, "singletons.fastq") + " "
            data_change_repop_mRNA += os.path.join(final_folder, "rRNA_filter_to_repop_mRNA_singletons.tsv")
        elif(self.read_mode == "paired"):
            data_change_repop_mRNA += os.path.join(dep_loc, "pair_1.fastq") + " "
            data_change_repop_mRNA += os.path.join(final_folder, "pair_1.fastq") + " "
            data_change_repop_mRNA += os.path.join(final_folder, "rRNA_filter_to_repop_mRNA_pair_1.tsv")    

        if self.read_mode == "single":
            COMMANDS_Repopulate = [
                repop_singletons,
                repop_singletons_rRNA#,
                #data_change_repop_mRNA,
                #data_change_repop_rRNA
            ]
        elif self.read_mode == "paired":
            COMMANDS_Repopulate = [
                repop_singletons,
                repop_singletons_rRNA,
                repop_pair_1,
                repop_pair_1_rRNA,
                repop_pair_2,
                repop_pair_2_rRNA,
                singleton_repop_filter,
                singleton_repop_filter_rRNA#,
                #data_change_repop_mRNA,
                #data_change_repop_rRNA
            ]

        return COMMANDS_Repopulate

    def create_assemble_contigs_command(self, stage_name, dependency_stage_name):
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        dep_loc             = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        spades_folder       = os.path.join(data_folder, "0_spades")
        mgm_folder          = os.path.join(data_folder, "1_mgm")
        bwa_folder          = os.path.join(data_folder, "2_bwa_align")
        sam_trimmer_folder  = os.path.join(data_folder, "3_clean_sam")
        mapped_reads_folder = os.path.join(data_folder, "4_mapped_reads")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(spades_folder)
        self.make_folder(bwa_folder)
        self.make_folder(sam_trimmer_folder)
        self.make_folder(mapped_reads_folder)
        self.make_folder(mgm_folder)
        self.make_folder(final_folder)

        # this assembles contigs
        spades = ">&2 echo Spades Contig assembly | "
        spades += self.tool_path_obj.Python + " "
        spades += self.tool_path_obj.Spades + " --rna"
        if self.read_mode == "paired":
            spades += " -1 " + os.path.join(dep_loc, "pair_1.fastq")  # in1 (pair 1)
            spades += " -2 " + os.path.join(dep_loc, "pair_2.fastq")  # in2 (pair 2)
        spades += " -s " + os.path.join(dep_loc, "singletons.fastq")  # in_single (singletons)
        spades += " -o " + spades_folder  # out

        #if there is no output, bypass contigs. -> But this is a v2 upgrade.  
        spades_rename = "cp " + os.path.join(spades_folder, "transcripts.fasta") + " " + os.path.join(spades_folder, "contigs.fasta")  # rename output
        
        original_contigs    = os.path.join(spades_folder, "contigs.fasta") 
        post_mgm_contig     = os.path.join(mgm_folder, "disassembled_contigs.fasta")
        mgm_report          = os.path.join(mgm_folder, "gene_report.txt")
        final_contigs       = os.path.join(mgm_folder, "contigs.fasta")
        
        #-------------------------------------------------------
        #spades does too good of a job sometimes.  Disassemble it into genes.
        disassemble_contigs = ">&2 echo Disassembling contigs | "
        disassemble_contigs += self.tool_path_obj.MetaGeneMark + " -o " + mgm_report + " "
        disassemble_contigs += "-D " + post_mgm_contig + " "
        disassemble_contigs += "-m " + self.tool_path_obj.mgm_model + " "
        disassemble_contigs += os.path.join(spades_folder, "contigs.fasta")
        
        remove_whitespace = ">&2 echo Removing whitespace from fasta | " 
        remove_whitespace += self.tool_path_obj.Python + " " + self.tool_path_obj.remove_gaps_in_fasta + " "
        remove_whitespace += post_mgm_contig + " "
        remove_whitespace += final_contigs
        

        #bwa_index = self.tool_path_obj.BWA + " index -a bwtsw " + final_contigs
        bwa_index = self.tool_path_obj.BWA + " index -a bwtsw " + original_contigs
        
        
        # Build a report of what was consumed by contig transmutation (assemble/disassemble)
        bwa_pair_1_contigs = ">&2 echo BWA pair contigs | "
        bwa_pair_1_contigs += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " -B 40 -O 60 -E 10 -L 50 "
        #bwa_pair_1_contigs += final_contigs + " "
        bwa_pair_1_contigs += original_contigs + " "
        bwa_pair_1_contigs += os.path.join(dep_loc, "pair_1.fastq")
        bwa_pair_1_contigs += " > " + os.path.join(bwa_folder, "pair_1.sam")

        bwa_pair_2_contigs = ">&2 echo BWA pair contigs | "
        bwa_pair_2_contigs += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " -B 40 -O 60 -E 10 -L 50 "
        #bwa_pair_2_contigs += final_contigs + " "
        bwa_pair_2_contigs += original_contigs + " "
        bwa_pair_2_contigs += os.path.join(dep_loc, "pair_2.fastq")
        bwa_pair_2_contigs += " > " + os.path.join(bwa_folder, "pair_2.sam")

        bwa_singletons_contigs = ">&2 echo BWA singleton contigs | "
        bwa_singletons_contigs += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " -B 40 -O 60 -E 10 -L 50 "
        #bwa_singletons_contigs += final_contigs + " "
        bwa_singletons_contigs += original_contigs + " "
        bwa_singletons_contigs += os.path.join(dep_loc, "singletons.fastq")
        bwa_singletons_contigs += " > " + os.path.join(bwa_folder, "singletons.sam")

        sam_trimmer_singletons = ">&2 echo cleaning up singletons sam | "
        sam_trimmer_singletons += self.tool_path_obj.Python + " " + self.tool_path_obj.sam_trimmer + " "
        sam_trimmer_singletons += os.path.join(bwa_folder, "singletons.sam") + " "
        sam_trimmer_singletons += os.path.join(sam_trimmer_folder, "singletons.sam")

        sam_trimmer_pair_1 = ">&2 echo cleaning up pair 1 sam | "
        sam_trimmer_pair_1 += self.tool_path_obj.Python + " " + self.tool_path_obj.sam_trimmer + " "
        sam_trimmer_pair_1 += os.path.join(bwa_folder, "pair_1.sam") + " "
        sam_trimmer_pair_1 += os.path.join(sam_trimmer_folder, "pair_1.sam")

        sam_trimmer_pair_2 = ">&2 echo cleaning up pair 2 sam | "
        sam_trimmer_pair_2 += self.tool_path_obj.Python + " " + self.tool_path_obj.sam_trimmer + " "
        sam_trimmer_pair_2 += os.path.join(bwa_folder, "pair_2.sam") + " "
        sam_trimmer_pair_2 += os.path.join(sam_trimmer_folder, "pair_2.sam")

        contig_duplicate_remover_singletons = ">&2 echo Removing consumed contigs from data | "
        contig_duplicate_remover_singletons += self.tool_path_obj.Python + " " + self.tool_path_obj.contig_duplicate_remover + " "
        contig_duplicate_remover_singletons += os.path.join(dep_loc, "singletons.fastq") + " "
        contig_duplicate_remover_singletons += os.path.join(sam_trimmer_folder, "singletons.sam") + " "
        contig_duplicate_remover_singletons += mapped_reads_folder

        contig_duplicate_remover_pair_1 = ">&2 echo Removing consumed contigs from data | "
        contig_duplicate_remover_pair_1 += self.tool_path_obj.Python + " " + self.tool_path_obj.contig_duplicate_remover + " "
        contig_duplicate_remover_pair_1 += os.path.join(dep_loc, "pair_1.fastq") + " "
        contig_duplicate_remover_pair_1 += os.path.join(sam_trimmer_folder, "pair_1.sam") + " "
        contig_duplicate_remover_pair_1 += mapped_reads_folder

        contig_duplicate_remover_pair_2 = ">&2 echo Removing consumed contigs from data | "
        contig_duplicate_remover_pair_2 += self.tool_path_obj.Python + " " + self.tool_path_obj.contig_duplicate_remover + " "
        contig_duplicate_remover_pair_2 += os.path.join(dep_loc, "pair_2.fastq") + " "
        contig_duplicate_remover_pair_2 += os.path.join(sam_trimmer_folder, "pair_2.sam") + " "
        contig_duplicate_remover_pair_2 += mapped_reads_folder

        map_read_contig = ">&2 echo map read contig v2 | "
        map_read_contig += self.tool_path_obj.Python + " " + self.tool_path_obj.map_contig + " "
        map_read_contig += os.path.join(final_folder, "contig_map.tsv") + " "
        map_read_contig += os.path.join(sam_trimmer_folder, "singletons.sam")
        if self.read_mode == "paired":
            map_read_contig += " " + os.path.join(sam_trimmer_folder, "pair_1.sam")
            map_read_contig += " " + os.path.join(sam_trimmer_folder, "pair_2.sam")

        copy_singletons = ">&2 echo Copying singletons to final folder | "
        copy_singletons += "cp " + os.path.join(mapped_reads_folder, "singletons.fastq") + " " + final_folder

        copy_contigs = ">&2 echo Copying contigs to final folder | "
        copy_contigs += "cp " + final_contigs + " " + final_folder

        singleton_assembly_filter = ">&2 echo filtering paired reads for singletons | "
        singleton_assembly_filter += self.tool_path_obj.Python + " "
        singleton_assembly_filter += self.tool_path_obj.orphaned_read_filter + " "
        singleton_assembly_filter += os.path.join(mapped_reads_folder, "pair_1.fastq") + " "
        singleton_assembly_filter += os.path.join(mapped_reads_folder, "pair_2.fastq") + " "
        singleton_assembly_filter += os.path.join(mapped_reads_folder, "singletons.fastq") + " "
        singleton_assembly_filter += os.path.join(final_folder, "pair_1.fastq") + " "
        singleton_assembly_filter += os.path.join(final_folder, "pair_2.fastq") + " "
        singleton_assembly_filter += os.path.join(final_folder, "singletons.fastq") + " "

        sort_paired = ">&2 echo sorting paired reads | "
        sort_paired += self.tool_path_obj.Python + " " + self.tool_path_obj.sort_reads + " "
        sort_paired += os.path.join(final_folder, "pair_1.fastq") + " "
        sort_paired += os.path.join(final_folder, "pair_1_sorted.fastq") + " | "
        sort_paired += self.tool_path_obj.Python + " " + self.tool_path_obj.sort_reads + " "
        sort_paired += os.path.join(final_folder, "pair_2.fastq") + " "
        sort_paired += os.path.join(final_folder, "pair_2_sorted.fastq")
        
        data_change_contig = ">&2 echo checking relative change in data between repop and contig assembly | "
        data_change_contig += self.tool_path_obj.Python + " "
        data_change_contig += self.tool_path_obj.data_change_metrics + " "
        if(self.read_mode == "single"):
            data_change_contig += os.path.join(dep_loc, "singletons.fastq") + " "
            data_change_contig += os.path.join(final_folder, "singletons.fastq") + " "
            data_change_contig += os.path.join(final_folder, "repop_to_contigs_singletons.tsv")
        elif(self.read_mode == "paired"):
            data_change_contig += os.path.join(dep_loc, "pair_1.fastq") + " "
            data_change_contig += os.path.join(final_folder, "pair_1.fastq") + " "
            data_change_contig += os.path.join(final_folder, "repop_to_contigs_pair_1.tsv")
            
        move_gene_report = ">&2 echo moving gene report | "
        move_gene_report += "cp" + " "
        move_gene_report += os.path.join(mgm_folder, "gene_report.txt") + " "
        move_gene_report += os.path.join(final_folder, "gene_report.txt") 
            

        if self.read_mode == "single":
            COMMANDS_Assemble = [
                spades,
                spades_rename,
                disassemble_contigs,
                remove_whitespace,
                bwa_index,
                bwa_singletons_contigs,
                sam_trimmer_singletons,
                contig_duplicate_remover_singletons,
                map_read_contig,
                copy_singletons,
                copy_contigs,
                move_gene_report
                #data_change_contig
            ]
        elif self.read_mode == "paired":
            COMMANDS_Assemble = [
                spades,
                spades_rename,
                disassemble_contigs,
                remove_whitespace,
                bwa_index,
                bwa_pair_1_contigs,
                bwa_pair_2_contigs,
                bwa_singletons_contigs,
                sam_trimmer_singletons,
                sam_trimmer_pair_1,
                sam_trimmer_pair_2,
                contig_duplicate_remover_singletons,
                contig_duplicate_remover_pair_1,
                contig_duplicate_remover_pair_2,
                map_read_contig,
                copy_contigs,
                singleton_assembly_filter,
                sort_paired,
                move_gene_report
                #data_change_contig
            ]

        return COMMANDS_Assemble

   
    def create_split_ga_fastq_data_command(self, stage_name, dependency_stage_name, category):
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        split_folder    = os.path.join(data_folder, "0_read_split", category)
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(split_folder)
        
        split_fastq = ">&2 echo splitting fastq for " + category + " | "
        split_fastq += "split -l " + str(int(self.chunk_size) * 4) + " "        
        split_fastq += os.path.join(dep_loc, category + ".fastq") + " "
        split_fastq += "--additional-suffix .fastq" + " "
        split_fastq += "-d" + " "
        split_fastq += os.path.join(split_folder, category + "_")
        
        COMMANDS_GA_prep_fastq = [
            split_fastq
        ]
        
        return COMMANDS_GA_prep_fastq

    def create_split_ga_fasta_data_command(self, stage_name, dependency_stage_name, category):
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        split_folder    = os.path.join(data_folder, "0_read_split", category)
        dep_folder      = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(split_folder)
        
        
        
        split_fasta = ">&2 echo splitting fasta for " + category + " | "
        split_fasta += self.tool_path_obj.Python + " "    
        split_fasta += self.tool_path_obj.File_splitter + " "
        split_fasta += os.path.join(dep_folder, category +".fasta") + " "
        split_fasta += os.path.join(split_folder, category) + " "
        split_fasta += self.chunk_size
        
        COMMANDS_GA_prep_fasta = [
            split_fasta
        ]
        
        return COMMANDS_GA_prep_fasta

    def create_BWA_annotate_command(self, stage_name, dependency_stage_name, section):
        # meant to be called multiple times: section -> contigs, singletons, pair_1, pair_2
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        bwa_folder      = os.path.join(data_folder, "0_bwa")
        final_folder    = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(bwa_folder)
        self.make_folder(final_folder)

        if section == "contigs":
            section_file = section + ".fasta"
        else:
            section_file = section + ".fastq"

        bwa_job = ">&2 echo BWA on " + section + " | "
        bwa_job += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " "
        bwa_job += self.tool_path_obj.DNA_DB + " "
        bwa_job += os.path.join(dep_loc, section_file) + " | "
        bwa_job += self.tool_path_obj.SAMTOOLS + " view "
        bwa_job += "> " + os.path.join(bwa_folder, section + ".sam")
        

        COMMANDS_BWA = [
            bwa_job
        ]

        return COMMANDS_BWA

    def create_BWA_annotate_command_v2(self, stage_name, query_file):
        # meant to be called multiple times: query file is a split file
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        bwa_folder      = os.path.join(data_folder, "1_bwa")
        

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(bwa_folder)

        file_tag = os.path.basename(query_file)
        file_tag = os.path.splitext(file_tag)[0]
        
        bwa_job = ">&2 echo BWA on " + file_tag + " | "
        bwa_job += self.tool_path_obj.BWA + " mem -t " + self.Threads_str + " "
        bwa_job += self.tool_path_obj.DNA_DB + " "
        #bwa_job += os.path.join(dep_loc, section_file) + " | "
        bwa_job += query_file + " | "
        bwa_job += self.tool_path_obj.SAMTOOLS + " view "
        bwa_job += "> " + os.path.join(bwa_folder, file_tag + ".sam")
        

        COMMANDS_BWA = [
            bwa_job
        ]

        return COMMANDS_BWA


    def create_BWA_pp_command(self, stage_name, dependency_stage_name):
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        bwa_folder      = os.path.join(data_folder, "0_bwa")
        final_folder    = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(bwa_folder)
        self.make_folder(final_folder)

        map_read_bwa = ">&2 echo map read bwa v2 | "
        map_read_bwa += self.tool_path_obj.Python + " "
        map_read_bwa += self.tool_path_obj.Map_reads_gene_BWA + " "
        map_read_bwa += self.tool_path_obj.DNA_DB + " "  # IN
        map_read_bwa += os.path.join(dep_loc, "contig_map.tsv") + " "  # IN
        map_read_bwa += os.path.join(final_folder, "gene_map.tsv") + " "  # OUT
        map_read_bwa += os.path.join(dep_loc, "contigs.fasta") + " "  # IN
        map_read_bwa += os.path.join(bwa_folder, "contigs.sam") + " "  # IN
        map_read_bwa += os.path.join(final_folder, "contigs.fasta") + " "  # OUT
        map_read_bwa += os.path.join(dep_loc, "singletons.fastq") + " "  # IN
        map_read_bwa += os.path.join(bwa_folder, "singletons.sam") + " "  # IN
        map_read_bwa += os.path.join(final_folder, "singletons.fasta")  # OUT
        if self.read_mode == "paired":
            map_read_bwa += " " + os.path.join(dep_loc, "pair_1.fastq") + " "  # IN
            map_read_bwa += os.path.join(bwa_folder, "pair_1.sam") + " "  # IN
            map_read_bwa += os.path.join(final_folder, "pair_1.fasta") + " "  # OUT
            map_read_bwa += os.path.join(dep_loc, "pair_2.fastq") + " "  # IN
            map_read_bwa += os.path.join(bwa_folder, "pair_2.sam") + " "  # IN
            map_read_bwa += os.path.join(final_folder, "pair_2.fasta")  # OUT

        copy_contig_map = ">&2 echo copy contig map | "
        copy_contig_map += "cp " + os.path.join(dep_loc, "contig_map.tsv") + " " + os.path.join(final_folder, "contig_map.tsv")

        COMMANDS_Annotate_BWA = [
            map_read_bwa,
            copy_contig_map
        ]

        return COMMANDS_Annotate_BWA
        
        
    def create_BWA_pp_command_v2(self, stage_name, dependency_stage_name, query_file):
        sample_root_name = os.path.basename(query_file)
        sample_root_name = os.path.splitext(sample_root_name)[0]
            
        
        #meant to be called on the split-file version.  PP script will not merge gene maps.
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        bwa_folder      = os.path.join(data_folder, "1_bwa")
        split_folder    = os.path.join(data_folder, "0_read_split")
        final_folder    = os.path.join(subfolder, "final_results")
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(bwa_folder)
        self.make_folder(final_folder)
        
        reads_in    = query_file
        bwa_in      = os.path.join(bwa_folder, sample_root_name + ".sam")
        reads_out = os.path.join(final_folder, sample_root_name + ".fasta")
            
        map_read_bwa = ">&2 echo GA BWA PP generic | "
        map_read_bwa += self.tool_path_obj.Python + " "
        map_read_bwa += self.tool_path_obj.Map_reads_gene_BWA + " "
        map_read_bwa += self.tool_path_obj.DNA_DB + " "  # IN
        map_read_bwa += os.path.join(dep_loc, "contig_map.tsv") + " "  # IN
        map_read_bwa += os.path.join(final_folder, sample_root_name + "_gene_map.tsv") + " "  # OUT
        map_read_bwa += os.path.join(final_folder, sample_root_name + "_mapped_genes.fna") + " " #OUT
        map_read_bwa += reads_in + " "
        map_read_bwa += bwa_in + " "
        map_read_bwa += reads_out
        
        

        COMMANDS_Annotate_BWA = [
            map_read_bwa,
            #copy_contig_map
        ]
        return COMMANDS_Annotate_BWA

    def create_BWA_copy_contig_map_command(self, stage_name, dependency_stage_name):
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        bwa_folder      = os.path.join(data_folder, "1_bwa")
        split_folder    = os.path.join(data_folder, "0_read_split")
        final_folder    = os.path.join(subfolder, "final_results")
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(bwa_folder)
        self.make_folder(final_folder)
    
        copy_contig_map = ">&2 echo copy contig map | "
        copy_contig_map += "cp " + os.path.join(dep_loc, "contig_map.tsv") + " " + os.path.join(final_folder, "contig_map.tsv")
        
        return [copy_contig_map]

    def create_BLAT_annotate_command(self, stage_name, dependency_stage_name, section, fasta):
        subfolder   = os.path.join(self.Output_Path, stage_name)
        data_folder = os.path.join(subfolder, "data")
        dep_loc     = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        blat_folder = os.path.join(data_folder, "0_blat")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(blat_folder)

        blat_command = ">&2 echo BLAT annotation for " + section + " " + fasta + " | "
        blat_command += self.tool_path_obj.BLAT + " -noHead -minIdentity=90 -minScore=65 "
        blat_command += self.tool_path_obj.DNA_DB_Split + fasta + " "
        blat_command += os.path.join(dep_loc, section + ".fasta")
        blat_command += " -fine -q=rna -t=dna -out=blast8 -threads=2" + " "
        blat_command += os.path.join(blat_folder, section + "_" + fasta + ".blatout")

        return [blat_command]
        
    def create_BLAT_annotate_command_v2(self, stage_name, query_file, fasta_db):
        #takes in a sample query file (expecting a segment of the whole GA data, after BWA
        sample_root_name = os.path.basename(query_file)
        sample_root_name = os.path.splitext(sample_root_name)[0]
        
        subfolder   = os.path.join(self.Output_Path, stage_name)
        data_folder = os.path.join(subfolder, "data")
        blat_folder = os.path.join(data_folder, "0_blat")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(blat_folder)

        blat_command = ">&2 echo BLAT annotation for " + sample_root_name + " " + fasta_db + " | "
        blat_command += self.tool_path_obj.BLAT + " -noHead -minIdentity=90 -minScore=65 "
        blat_command += self.tool_path_obj.DNA_DB_Split + fasta_db + " "
        blat_command += query_file
        blat_command += " -fine -q=rna -t=dna -out=blast8 -threads=2" + " "
        blat_command += os.path.join(blat_folder, sample_root_name + "_" + fasta_db + ".blatout")
        
        if(os.path.getsize(query_file) > 0):
            return [blat_command]
        else:
            dummy_blat_command = ">&2 echo Not running BLAT command on empty file: " + query_file
            return [dummy_blat_command]
        
        

    def create_BLAT_cat_command(self, stage_name, section):
        # this is meant to be called for each section: contigs, singletons, pair_1, pair_2
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        blat_folder         = os.path.join(data_folder, "0_blat")
        blat_merge_folder   = os.path.join(data_folder, "1_blat_merge")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(blat_merge_folder)

        cat_command = "cat " + os.path.join(blat_folder, section + "*.blatout") + " > " + os.path.join(blat_merge_folder, section + ".blatout")
        return [cat_command]
        
    def create_BLAT_cat_command_v2(self, stage_name, query_file):
        sample_root_name = os.path.basename(query_file)
        sample_root_name = os.path.splitext(sample_root_name)[0]
        # This merges each blatout file based on the sample's name
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        blat_folder         = os.path.join(data_folder, "0_blat")
        blat_merge_folder   = os.path.join(data_folder, "1_blat_merge")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(blat_merge_folder)

        #cat_command = "cat " + os.path.join(blat_folder, sample_root_name + "*.blatout") + " > " + os.path.join(blat_merge_folder, sample_root_name + ".blatout")
        cat_command = "for f in " + os.path.join(blat_folder, sample_root_name + "_*.blatout") + ";  do cat $f >> " + os.path.join(blat_merge_folder, sample_root_name + ".blatout") + " && rm $f; done"
        #cleanup_command = "rm " + os.path.join(blat_folder, sample_root_name + "*.blatout")
        cleanup_command = "for f in " + os.path.join(blat_folder, sample_root_name + "_*.blatout") + "; do rm $f; done"
        return [
            cat_command
            #cleanup_command
        ]
        
        

    def create_BLAT_pp_command(self, stage_name, dependency_stage_name):
        # this call is meant to be run after the BLAT calls have been completed.
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        dep_loc             = os.path.join(self.Output_Path, dependency_stage_name, "final_results")  # implied to be BWA
        blat_merge_folder   = os.path.join(data_folder, "1_blat_merge")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)

        blat_pp = ">&2 echo BLAT post-processing | "
        blat_pp += self.tool_path_obj.Python + " "
        blat_pp += self.tool_path_obj.Map_reads_gene_BLAT + " "
        blat_pp += self.tool_path_obj.DNA_DB + " "
        blat_pp += os.path.join(dep_loc, "contig_map.tsv") + " "
        blat_pp += os.path.join(dep_loc, "gene_map.tsv") + " "
        blat_pp += os.path.join(final_folder, "genes.fna") + " "
        blat_pp += os.path.join(final_folder, "gene_map.tsv") + " "
        blat_pp += os.path.join(final_folder, "genes.fna") + " "
        blat_pp += os.path.join(dep_loc, "contigs.fasta") + " "
        blat_pp += os.path.join(blat_merge_folder, "contigs.blatout") + " "
        blat_pp += os.path.join(final_folder, "contigs.fasta") + " "
        blat_pp += os.path.join(dep_loc, "singletons.fasta") + " "
        blat_pp += os.path.join(blat_merge_folder, "singletons.blatout") + " "
        blat_pp += os.path.join(final_folder, "singletons.fasta")
        if self.read_mode == "paired":
            blat_pp += " " + os.path.join(dep_loc, "pair_1.fasta") + " "
            blat_pp += os.path.join(blat_merge_folder, "pair_1.blatout") + " "
            blat_pp += os.path.join(final_folder, "pair_1.fasta") + " "
            blat_pp += os.path.join(dep_loc, "pair_2.fasta") + " "
            blat_pp += os.path.join(blat_merge_folder, "pair_2.blatout") + " "
            blat_pp += os.path.join(final_folder, "pair_2.fasta")

        copy_contig_map = ">&2 echo copy contig map | "
        copy_contig_map += "cp " + os.path.join(dep_loc, "contig_map.tsv") + " " + os.path.join(final_folder, "contig_map.tsv")

        COMMANDS_Annotate_BLAT_Post = [
            blat_pp,
            copy_contig_map
        ]

        return COMMANDS_Annotate_BLAT_Post

    def create_BLAT_pp_command_v2(self, stage_name, query_file, dependency_stage_name):
        # this call is meant to be run after the BLAT calls have been completed.
        
        sample_root_name = os.path.basename(query_file)
        sample_root_name = os.path.splitext(sample_root_name)[0]
        
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        blat_folder         = os.path.join(data_folder, "1_blat_merge")
        final_folder        = os.path.join(subfolder, "final_results")
        dep_loc             = os.path.join(self.Output_Path, dependency_stage_name, "final_results")  # implied to be BWA

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(blat_folder)
        self.make_folder(final_folder)

        blat_pp = ">&2 echo BLAT post-processing | "
        blat_pp += self.tool_path_obj.Python + " "
        blat_pp += self.tool_path_obj.Map_reads_gene_BLAT + " "
        blat_pp += self.tool_path_obj.DNA_DB + " "
        blat_pp += os.path.join(dep_loc, "contig_map.tsv") + " "
        blat_pp += os.path.join(final_folder, sample_root_name + "_mapped_genes.fna") + " "
        blat_pp += os.path.join(final_folder, sample_root_name + "_gene_map.tsv") + " "
        blat_pp += query_file + " "
        blat_pp += os.path.join(blat_folder, sample_root_name + ".blatout") + " "
        blat_pp += os.path.join(final_folder, sample_root_name + ".fasta") + " "
        


        COMMANDS_Annotate_BLAT_Post = [
            blat_pp
        ]

        return COMMANDS_Annotate_BLAT_Post

    def create_BLAT_copy_contig_map_command(self, stage_name, dependency_stage_name):
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        final_folder    = os.path.join(subfolder, "final_results")
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        #self.make_folder(bwa_folder)
        self.make_folder(final_folder)
    
        copy_contig_map = ">&2 echo copy contig map | "
        copy_contig_map += "cp " + os.path.join(dep_loc, "contig_map.tsv") + " " + os.path.join(final_folder, "contig_map.tsv")
        
        return [copy_contig_map]


    def create_DIAMOND_annotate_command(self, stage_name, dependency_stage_name, section):
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        dep_loc             = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        diamond_folder      = os.path.join(data_folder, "0_diamond")
        section_folder      = os.path.join(data_folder, section)
        section_temp_folder = os.path.join(section_folder, "temp")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(diamond_folder)
        self.make_folder(section_folder)
        self.make_folder(section_temp_folder)

        diamond_annotate = ">&2 echo gene annotate DIAMOND " + section + " | "
        diamond_annotate += self.tool_path_obj.DIAMOND
        diamond_annotate += " blastx -p " + self.Threads_str
        diamond_annotate += " -d " + self.tool_path_obj.Prot_DB
        diamond_annotate += " -q " + os.path.join(dep_loc, section + ".fasta")
        diamond_annotate += " -o " + os.path.join(diamond_folder, section + ".dmdout")
        diamond_annotate += " -f 6 -t " + section_temp_folder
        diamond_annotate += " -k 10 --id 85 --query-cover 65 --min-score 60 --unal 1"

        return [diamond_annotate]
        
    def create_DIAMOND_annotate_command_v2(self, stage_name, query_file):
        sample_root_name = os.path.basename(query_file)
        sample_root_name = os.path.splitext(sample_root_name)[0]
    
        subfolder           = os.path.join(self.Output_Path, stage_name)
        data_folder         = os.path.join(subfolder, "data")
        #dep_loc             = os.path.join(self.Output_Path, dependency_stage_name, "final_results")
        diamond_folder      = os.path.join(data_folder, "0_diamond")
        main_temp_folder    = os.path.join(data_folder, sample_root_name + "_diamond_temp")
        temp_folder =       os.path.join(main_temp_folder, "temp")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(diamond_folder)
        self.make_folder(main_temp_folder)
        self.make_folder(temp_folder)
        
        diamond_annotate = ">&2 echo gene annotate DIAMOND " + sample_root_name + " | "
        diamond_annotate += self.tool_path_obj.DIAMOND
        diamond_annotate += " blastx -p " + self.Threads_str
        diamond_annotate += " -d " + self.tool_path_obj.Prot_DB
        diamond_annotate += " -q " + query_file 
        diamond_annotate += " -o " + os.path.join(diamond_folder, sample_root_name + ".dmdout")
        diamond_annotate += " -f 6 -t " + temp_folder #section_temp_folder
        diamond_annotate += " -k 10 --id 85 --query-cover 65 --min-score 60 --unal 1"

        return [diamond_annotate]


    def create_DIAMOND_pp_command(self, stage_name, dependency_0_stage_name):
        # the command just calls the merger program
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        dep_loc_0       = os.path.join(self.Output_Path, dependency_0_stage_name, "final_results")  # implied to be blat pp
        diamond_folder  = os.path.join(data_folder, "0_diamond/")
        final_folder    = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)

        diamond_pp = ">&2 echo DIAMOND post process | "
        diamond_pp += self.tool_path_obj.Python + " "
        diamond_pp += self.tool_path_obj.Map_reads_prot_DMND + " "
        diamond_pp += self.tool_path_obj.Prot_DB_reads + " "  # IN
        diamond_pp += os.path.join(dep_loc_0, "contig_map.tsv") + " "  # IN
        diamond_pp += os.path.join(dep_loc_0, "gene_map.tsv") + " "  # IN
        diamond_pp += os.path.join(final_folder, "gene_map.tsv") + " "  # OUT
        diamond_pp += os.path.join(dep_loc_0, "genes.fna") + " "  # IN
        diamond_pp += os.path.join(final_folder, "proteins.faa") + " "  # OUT
        diamond_pp += os.path.join(dep_loc_0, "contigs.fasta") + " "  # IN
        diamond_pp += os.path.join(diamond_folder, "contigs.dmdout") + " "  # IN
        diamond_pp += os.path.join(final_folder, "contigs.fasta") + " "  # OUT
        diamond_pp += os.path.join(dep_loc_0, "singletons.fasta") + " "  # IN
        diamond_pp += os.path.join(diamond_folder, "singletons.dmdout") + " "  # IN
        diamond_pp += os.path.join(final_folder, "singletons.fasta")  # OUT
        if self.read_mode == "paired":
            diamond_pp += " " + os.path.join(dep_loc_0, "pair_1.fasta") + " "  # IN
            diamond_pp += os.path.join(diamond_folder, "pair_1.dmdout") + " "  # IN
            diamond_pp += os.path.join(final_folder, "pair_1.fasta") + " "  # OUT
            diamond_pp += os.path.join(dep_loc_0, "pair_2.fasta") + " "  # IN
            diamond_pp += os.path.join(diamond_folder, "pair_2.dmdout") + " "  # IN
            diamond_pp += os.path.join(final_folder, "pair_2.fasta")  # OUT

        COMMANDS_Annotate_Diamond_Post = [
            diamond_pp
        ]

        return COMMANDS_Annotate_Diamond_Post
        
    def create_DIAMOND_pp_command_v2(self, stage_name, dependency_stage_name, query_file):
    
        sample_root_name = os.path.basename(query_file)
        sample_root_name = os.path.splitext(sample_root_name)[0]
        # the command just calls the merger program
        subfolder       = os.path.join(self.Output_Path, stage_name)
        data_folder     = os.path.join(subfolder, "data")
        dep_loc         = os.path.join(self.Output_Path, dependency_stage_name, "final_results")  # implied to be blat pp
        diamond_folder  = os.path.join(data_folder, "0_diamond/")
        final_folder    = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)

        diamond_pp = ">&2 echo DIAMOND post process | "
        diamond_pp += self.tool_path_obj.Python + " "
        diamond_pp += self.tool_path_obj.Map_reads_prot_DMND + " "
        diamond_pp += self.tool_path_obj.Prot_DB_reads + " "                # IN
        diamond_pp += os.path.join(dep_loc, "contig_map.tsv") + " "         # IN
        diamond_pp += os.path.join(final_folder, sample_root_name + "_diamond_gene_map.tsv") + " "      # OUT
        diamond_pp += os.path.join(final_folder, sample_root_name + "_diamond_proteins.faa") + " "      # OUT
        
        diamond_pp += query_file + " "                                                  # IN
        diamond_pp += os.path.join(diamond_folder, sample_root_name + ".dmdout") + " "  # IN
        diamond_pp += os.path.join(final_folder, sample_root_name + ".fasta") + " "     # OUT
        

        COMMANDS_Annotate_Diamond_Post = [
            diamond_pp
        ]

        return COMMANDS_Annotate_Diamond_Post 



    def create_GA_final_merge_command(self, current_stage_name, dep_0_name, dep_1_name, dep_2_name, dep_3_name):
        subfolder = os.path.join(self.Output_Path, current_stage_name)
        data_folder = os.path.join(subfolder, "data")
        final_folder = os.path.join(subfolder, "final_results")
        dep_0_path = os.path.join(self.Output_Path, dep_0_name, "final_results")
        dep_1_path = os.path.join(self.Output_Path, dep_1_name, "final_results")
        dep_2_path = os.path.join(self.Output_Path, dep_2_name, "final_results")
        dep_3_path = os.path.join(self.Output_Path, dep_3_name, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)
        
        final_merge = self.tool_path_obj.Python + " "
        final_merge += self.tool_path_obj.GA_final_merge + " "
        final_merge += dep_3_path + " "
        final_merge += dep_0_path + " "
        final_merge += dep_1_path + " "
        final_merge += dep_2_path + " "
        final_merge += data_folder + " "
        final_merge += final_folder
        
        COMMANDS_ga_final_merge = [
            final_merge
        ]
        
        return COMMANDS_ga_final_merge
        

        

    def create_taxonomic_annotation_command(self, current_stage_name, rRNA_stage, assemble_contigs_stage, ga_final_merge_stage):
        subfolder               = os.path.join(self.Output_Path, current_stage_name)
        data_folder             = os.path.join(subfolder, "data")
        rRNA_folder             = os.path.join(self.Output_Path, rRNA_stage, "final_results", "rRNA")
        assemble_contigs_folder = os.path.join(self.Output_Path, assemble_contigs_stage, "final_results")
        final_merge_folder      = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        ga_taxa_folder          = os.path.join(data_folder, "0_gene_taxa")
        kaiju_folder            = os.path.join(data_folder, "1_kaiju")
        centrifuge_folder       = os.path.join(data_folder, "2_centrifuge")
        wevote_folder           = os.path.join(data_folder, "3_wevote")
        final_folder            = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(ga_taxa_folder)
        self.make_folder(kaiju_folder)
        self.make_folder(centrifuge_folder)
        self.make_folder(wevote_folder)
        self.make_folder(rRNA_folder)
        self.make_folder(final_folder)

        get_taxa_from_gene = ">&2 echo get taxa from gene | "
        get_taxa_from_gene += self.tool_path_obj.Python + " "
        get_taxa_from_gene += self.tool_path_obj.Annotated_taxid + " "  # SLOW STEP
        get_taxa_from_gene += os.path.join(final_merge_folder, "gene_map.tsv") + " "
        get_taxa_from_gene += self.tool_path_obj.accession2taxid + " "
        get_taxa_from_gene += os.path.join(ga_taxa_folder, "ga_taxon.tsv")

        kaiju_on_contigs = ">&2 echo kaiju on contigs | "
        kaiju_on_contigs += self.tool_path_obj.Kaiju
        kaiju_on_contigs += " -t " + self.tool_path_obj.nodes
        kaiju_on_contigs += " -f " + self.tool_path_obj.Kaiju_db
        kaiju_on_contigs += " -i " + os.path.join(assemble_contigs_folder, "contigs.fasta")
        kaiju_on_contigs += " -z " + self.Threads_str
        kaiju_on_contigs += " -o " + os.path.join(kaiju_folder, "contigs.tsv")

        kaiju_on_singletons = ">&2 echo kaiju on singletons | "
        kaiju_on_singletons += self.tool_path_obj.Kaiju
        kaiju_on_singletons += " -t " + self.tool_path_obj.nodes
        kaiju_on_singletons += " -f " + self.tool_path_obj.Kaiju_db
        kaiju_on_singletons += " -i " + os.path.join(assemble_contigs_folder, "singletons.fastq")
        kaiju_on_singletons += " -z " + self.Threads_str
        kaiju_on_singletons += " -o " + os.path.join(kaiju_folder, "singletons.tsv")

        kaiju_on_paired = ">&2 echo kaiju on pairs | "
        kaiju_on_paired += self.tool_path_obj.Kaiju
        kaiju_on_paired += " -t " + self.tool_path_obj.nodes
        kaiju_on_paired += " -f " + self.tool_path_obj.Kaiju_db
        kaiju_on_paired += " -i " + os.path.join(assemble_contigs_folder, "pair_1.fastq")
        kaiju_on_paired += " -j " + os.path.join(assemble_contigs_folder, "pair_2.fastq")
        kaiju_on_paired += " -z " + self.Threads_str
        kaiju_on_paired += " -o " + os.path.join(kaiju_folder, "pairs.tsv")

        cat_kaiju = ">&2 echo merging all kaiju results | "
        cat_kaiju += "cat "
        cat_kaiju += os.path.join(kaiju_folder, "contigs.tsv") + " "
        cat_kaiju += os.path.join(kaiju_folder, "singletons.tsv")
        if self.read_mode == "paired":
            cat_kaiju += " " + os.path.join(kaiju_folder, "pairs.tsv")
        cat_kaiju += " > " + os.path.join(kaiju_folder, "merged_kaiju.tsv")

        centrifuge_on_reads = ">&2 echo centrifuge on reads | "
        centrifuge_on_reads += self.tool_path_obj.Centrifuge
        centrifuge_on_reads += " -x " + self.tool_path_obj.Centrifuge_db
        centrifuge_on_reads += " -U " + os.path.join(assemble_contigs_folder, "singletons.fastq")
        if self.read_mode == "paired":
            centrifuge_on_reads += " -1 " + os.path.join(assemble_contigs_folder, "pair_1.fastq")
            centrifuge_on_reads += " -2 " + os.path.join(assemble_contigs_folder, "pair_2.fastq")
        centrifuge_on_reads += " --exclude-taxids 2759 -k 1 --tab-fmt-cols " + "score,readID,taxID"
        centrifuge_on_reads += " --phred" + self.Qual_str
        centrifuge_on_reads += " -p 6"
        centrifuge_on_reads += " -S " + os.path.join(centrifuge_folder, "reads.tsv")
        centrifuge_on_reads += " --report-file " + os.path.join(centrifuge_folder, "reads.txt")

        centrifuge_on_contigs = ">&2 echo centrifuge on contigs | "
        centrifuge_on_contigs += self.tool_path_obj.Centrifuge
        centrifuge_on_contigs += " -f -x " + self.tool_path_obj.Centrifuge_db
        centrifuge_on_contigs += " -U " + os.path.join(assemble_contigs_folder, "contigs.fasta")
        centrifuge_on_contigs += " --exclude-taxids 2759 -k 1 --tab-fmt-cols " + "score,readID,taxID"
        centrifuge_on_contigs += " --phred" + self.Qual_str
        centrifuge_on_contigs += " -p 6"
        centrifuge_on_contigs += " -S " + os.path.join(centrifuge_folder, "contigs.tsv")
        centrifuge_on_contigs += " --report-file " + os.path.join(centrifuge_folder, "contigs.txt")

        cat_centrifuge = ">&2 echo combining all centrifuge results | "
        cat_centrifuge += "cat "
        cat_centrifuge += os.path.join(centrifuge_folder, "reads.tsv") + " "
        cat_centrifuge += os.path.join(centrifuge_folder, "contigs.tsv")
        cat_centrifuge += " > " + os.path.join(centrifuge_folder, "merged_centrifuge.tsv")

        wevote_combine = ">&2 echo combining classification outputs for wevote | "
        wevote_combine += self.tool_path_obj.Python + " "
        wevote_combine += self.tool_path_obj.Classification_combine + " "
        wevote_combine += os.path.join(assemble_contigs_folder, "contig_map.tsv")
        wevote_combine += " " + os.path.join(wevote_folder, "wevote_ensemble.csv") + " "
        wevote_combine += os.path.join(ga_taxa_folder, "ga_taxon.tsv") + " "
        wevote_combine += os.path.join(ga_taxa_folder, "ga_taxon.tsv") + " "
        wevote_combine += os.path.join(ga_taxa_folder, "ga_taxon.tsv") + " "
        wevote_combine += os.path.join(kaiju_folder, "merged_kaiju.tsv") + " "
        wevote_combine += os.path.join(centrifuge_folder, "merged_centrifuge.tsv")

        wevote_call = ">&2 echo Running WEVOTE | "
        wevote_call += self.tool_path_obj.WEVOTE
        wevote_call += " -i " + os.path.join(wevote_folder, "wevote_ensemble.csv")
        wevote_call += " -d " + self.tool_path_obj.WEVOTEDB
        wevote_call += " -p " + os.path.join(wevote_folder, "wevote")
        wevote_call += " -n " + self.Threads_str
        wevote_call += " -k " + "2"
        wevote_call += " -a " + "0"
        wevote_call += " -s " + "0"

        #awk_cleanup = ">&2 echo AWK cleanup of WEVOTE results | "
        #awk_cleanup += "awk -F \'\\t\' \'{print \"C\\t\"$1\"\\t\"$9}\' "
        #awk_cleanup += os.path.join(wevote_folder, "wevote_WEVOTE_Details.txt")
        #awk_cleanup += " > " + os.path.join(final_folder, "taxonomic_classifications.tsv")
        wevote_collect = ">&2 echo gathering WEVOTE results | "
        wevote_collect += self.tool_path_obj.Python + " "
        wevote_collect += self.tool_path_obj.Wevote_parser + " "
        wevote_collect += os.path.join(wevote_folder, "wevote_WEVOTE_Details.txt") + " "
        wevote_collect += os.path.join(final_folder, "taxonomic_classifications.tsv")
        

        centrifuge_on_rRNA = ">&2 echo centrifuge on rRNA | "
        centrifuge_on_rRNA += self.tool_path_obj.Centrifuge
        centrifuge_on_rRNA += " -x " + self.tool_path_obj.Centrifuge_db
        centrifuge_on_rRNA += " -U " + os.path.join(rRNA_folder, "singletons.fastq")
        if self.read_mode == "paired":
            centrifuge_on_rRNA += " -1 " + os.path.join(rRNA_folder, "pair_1.fastq")
            centrifuge_on_rRNA += " -2 " + os.path.join(rRNA_folder, "pair_2.fastq")
        centrifuge_on_rRNA += " --exclude-taxids 2759 -k 1 --tab-fmt-cols " + "score,readID,taxID"
        centrifuge_on_rRNA += " --phred" + self.Qual_str
        centrifuge_on_rRNA += " -p 6"
        centrifuge_on_rRNA += " -S " + os.path.join(final_folder, "rRNA.tsv")
        centrifuge_on_rRNA += " --report-file " + os.path.join(final_folder, "rRNA.txt")

        constrain = ">&2 echo Constraining the Taxonomic Annotation | " 
        constrain += self.tool_path_obj.Python + " " + self.tool_path_obj.Constrain_classification + " "
        constrain += self.tool_path_obj.target_rank + " "
        constrain += os.path.join(final_folder, "taxonomic_classifications.tsv") + " "
        constrain += self.tool_path_obj.nodes + " "
        constrain += self.tool_path_obj.names + " "
        constrain += os.path.join(final_folder, "constrain_classification.tsv")
        
        
        if self.read_mode == "single":
            COMMANDS_Classify = [
                get_taxa_from_gene,
                kaiju_on_contigs,
                kaiju_on_singletons,
                cat_kaiju,
                centrifuge_on_reads,
                centrifuge_on_contigs,
                cat_centrifuge,
                wevote_combine,
                wevote_call,
                wevote_collect,
                constrain
            ]
        elif self.read_mode == "paired":
            COMMANDS_Classify = [
                get_taxa_from_gene,
                kaiju_on_contigs,
                kaiju_on_singletons,
                kaiju_on_paired,
                cat_kaiju,
                centrifuge_on_reads,
                centrifuge_on_contigs,
                cat_centrifuge,
                wevote_combine,
                wevote_call,
                wevote_collect,
                centrifuge_on_rRNA,
                constrain
            ]

        return COMMANDS_Classify
        
      

    def create_EC_DETECT_command(self, current_stage_name, ga_final_merge_stage):
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        final_merge_folder  = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        detect_folder       = os.path.join(data_folder, "0_detect")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(detect_folder)
        
        detect_protein = ">&2 echo running detect on split file | "
        detect_protein += self.tool_path_obj.Python + " "
        detect_protein += self.tool_path_obj.Detect + " "
        detect_protein += os.path.join(final_merge_folder,"all_proteins.faa")
        detect_protein += " --output_file " + os.path.join(detect_folder, "proteins.detect")
        detect_protein += " --fbeta " + os.path.join(detect_folder, "proteins.fbeta")
        detect_protein += " --db " + self.tool_path_obj.DetectDB
        detect_protein += " --blastp " + self.tool_path_obj.Blastp
        detect_protein += " --needle " + self.tool_path_obj.Needle
        detect_protein += " --dump_dir " + detect_folder 
        detect_protein += " --n_count" + " " + str(self.tool_path_obj.DETECT_job_limit)
        detect_protein += " --mem_limit" + " " + str(self.tool_path_obj.DETECT_mem_threshold) 
        detect_protein += " --job_delay" + " " + str(self.tool_path_obj.DETECT_job_delay)
        detect_protein += " >> " + os.path.join(detect_folder, "detect_out.txt") + " 2>&1"

        COMMANDS_DETECT = [
            detect_protein
        ]

        return COMMANDS_DETECT

    def create_EC_PRIAM_command(self, current_stage_name, ga_final_merge_stage):
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        final_merge_folder  = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        PRIAM_folder        = os.path.join(data_folder, "1_priam")
        

        self.make_folder(PRIAM_folder)
        

        PRIAM_command = ">&2 echo running PRIAM | "
        PRIAM_command += self.tool_path_obj.Java + " "
        PRIAM_command += self.tool_path_obj.Priam
        PRIAM_command += " -n " + "proteins_priam" + " "
        PRIAM_command += " -i " + os.path.join(final_merge_folder, "all_proteins.faa")
        PRIAM_command += " -p " + self.tool_path_obj.PriamDB
        PRIAM_command += " -o " + PRIAM_folder
        PRIAM_command += " --np " + self.Threads_str
        PRIAM_command += " --bh --cc --cg --bp --bd "
        PRIAM_command += self.tool_path_obj.BLAST_dir

        COMMANDS_PRIAM = [
            PRIAM_command
        ]

        return COMMANDS_PRIAM
        
        
    def create_EC_DIAMOND_command(self, current_stage_name, ga_final_merge_stage):
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        final_merge_folder  = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        diamond_ea_folder   = os.path.join(data_folder, "2_diamond")
        
        self.make_folder(diamond_ea_folder)
        
        diamond_ea_command = ">&2 echo running Diamond enzyme annotation | "
        diamond_ea_command += self.tool_path_obj.DIAMOND + " blastp"
        diamond_ea_command += " -p " + self.Threads_str
        diamond_ea_command += " --query " + os.path.join(final_merge_folder, "all_proteins.faa")
        diamond_ea_command += " --db " + self.tool_path_obj.SWISS_PROT
        diamond_ea_command += " --outfmt " + "6 qseqid sseqid length qstart qend sstart send evalue bitscore qcovhsp slen pident"
        diamond_ea_command += " --out " + os.path.join(diamond_ea_folder, "proteins.blastout")
        diamond_ea_command += " --evalue 0.0000000001"
        #diamond_ea_command += " --max-target-seqs 1"
        
        COMMANDS_DIAMOND_EC = [
            diamond_ea_command
        ]
        
        return COMMANDS_DIAMOND_EC
        
    def create_EC_postprocess_command(self, current_stage_name, ga_final_merge_stage):
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        final_merge_folder  = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        detect_folder       = os.path.join(data_folder, "0_detect")
        PRIAM_folder        = os.path.join(data_folder, "1_priam")
        diamond_ea_folder   = os.path.join(data_folder, "2_diamond")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(final_folder)
        #combine_detect = "cat " + os.path.join(detect_folder, "protein_*.toppred")
        #combine_detect += " > " + os.path.join(detect_folder, "proteins.toppred")

        postprocess_command = ">&2 echo combining enzyme annotation output | "
        postprocess_command += self.tool_path_obj.Python + " "
        postprocess_command += self.tool_path_obj.EC_Annotation_Post + " "
        postprocess_command += os.path.join(detect_folder, "proteins.fbeta") + " "
        postprocess_command += os.path.join(PRIAM_folder, "PRIAM_proteins_priam", "ANNOTATION", "sequenceECs.txt") + " "
        postprocess_command += os.path.join(diamond_ea_folder, "proteins.blastout") + " "
        postprocess_command += self.tool_path_obj.SWISS_PROT_map + " "
        postprocess_command += os.path.join(final_merge_folder, "gene_map.tsv") + " "
        postprocess_command += self.tool_path_obj.enzyme_db + " "
        postprocess_command += os.path.join(final_folder, "proteins.ECs_All") + " "
        postprocess_command += os.path.join(final_folder, "lq_proteins.ECs_All")

        COMMANDS_EC_Postprocess = [
            #combine_detect,
            postprocess_command
        ]

        return COMMANDS_EC_Postprocess

        
    def create_output_taxa_table_v2_command(self, current_stage_name, assemble_contigs_stage, taxonomic_annotation_stage):
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        taxa_prep_folder    = os.path.join(data_folder, "3_taxa_table")
        contig_folder       = os.path.join(self.Output_Path, assemble_contigs_stage, "final_results")
        taxa_folder         = os.path.join(self.Output_Path, taxonomic_annotation_stage, "final_results")
        final_folder        = os.path.join(subfolder, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(taxa_prep_folder)
        self.make_folder(final_folder)
        
        copy_contig_data = ">&2 echo Copying contig data | "
        copy_contig_data += "cp" + " "
        copy_contig_data += os.path.join(contig_folder, "contigs.fasta") + " "
        copy_contig_data += taxa_prep_folder
        
        copy_constrain_class = ">&2 echo Copying constrain classification | "
        copy_constrain_class += "cp" + " "
        copy_constrain_class += os.path.join(taxa_folder, "constrain_classification.tsv") + " "
        copy_constrain_class += taxa_prep_folder
        
        bwa_index_contigs = ">&2 echo BWA index contigs | "
        bwa_index_contigs += self.tool_path_obj.BWA + " "
        bwa_index_contigs += "index" + " "
        bwa_index_contigs += os.path.join(taxa_prep_folder, "contigs.fasta")
        
        bwa_raw_on_contigs = ">&2 echo BWA raw on contigs | "
        bwa_raw_on_contigs += self.tool_path_obj.BWA + " "
        bwa_raw_on_contigs += "mem -t " + self.Threads_str + " "
        bwa_raw_on_contigs += os.path.join(taxa_prep_folder, "contigs.fasta") + " "
        if(self.read_mode == "single"):
            bwa_raw_on_contigs += self.sequence_single + " "
        else:
            bwa_raw_on_contigs += self.sequence_path_1 + " "
        bwa_raw_on_contigs += "> " + os.path.join(taxa_prep_folder, "raw_on_contigs.sam") + " "

        parse_sam = ">&2 echo parsing raw-on-contigs SAM | "
        parse_sam += self.tool_path_obj.Python + " "
        parse_sam += self.tool_path_obj.parse_sam + " "
        parse_sam += os.path.join(taxa_prep_folder, "raw_on_contigs.sam") + " "
        parse_sam += os.path.join(taxa_prep_folder, "contig_read_count.tsv") + " "
        parse_sam += os.path.join(taxa_prep_folder, "contig_read_list.tsv") + " "
        parse_sam += os.path.join(taxa_prep_folder, "contig_segment_read_map.tsv") 
        
        are_you_in_a_contig = ">&2 echo Sorting if a read is in a contig | "
        are_you_in_a_contig += self.tool_path_obj.Python + " "
        are_you_in_a_contig += self.tool_path_obj.are_you_in_a_contig + " "
        are_you_in_a_contig += os.path.join(taxa_prep_folder, "contig_read_list.tsv") + " "
        if(self.read_mode == "single"):
            are_you_in_a_contig += self.sequence_single + " "
        else:   
            are_you_in_a_contig += self.sequence_path_1 + " "
        are_you_in_a_contig += os.path.join(taxa_prep_folder, "read_contig_lookup.tsv") 

        clean_constrain_file = ">&2 echo Cleaning Constrain_classification | "
        clean_constrain_file += self.tool_path_obj.Python + " "
        clean_constrain_file += self.tool_path_obj.output_filter_taxa + " "
        clean_constrain_file += os.path.join(taxa_prep_folder, "constrain_classification.tsv") + " "
        clean_constrain_file += os.path.join(taxa_prep_folder, "contig_segment_read_map.tsv") + " "
        clean_constrain_file += os.path.join(taxa_prep_folder, "cleaned_constrain_classification.tsv")
        

        make_taxa_table = ">&2 echo Making taxa table | "
        make_taxa_table += self.tool_path_obj.Python + " "
        make_taxa_table += self.tool_path_obj.taxa_table + " "
        make_taxa_table += os.path.join(taxa_prep_folder, "cleaned_constrain_classification.tsv") + " "
        make_taxa_table += os.path.join(taxa_prep_folder, "contig_read_count.tsv") + " "
        make_taxa_table += os.path.join(taxa_prep_folder, "read_contig_lookup.tsv") + " "
        make_taxa_table += os.path.join(final_folder, "taxa_table.tsv")
        
        

        command_list = [
            copy_contig_data, 
            copy_constrain_class,
            bwa_index_contigs,
            bwa_raw_on_contigs,
            parse_sam,
            are_you_in_a_contig,
            clean_constrain_file,
            make_taxa_table
        ]
        
        return command_list
        

        
    def create_output_copy_gene_map_command(self, current_stage_name, ga_final_merge_stage):
        #must use the contig map from output_taxa_table.
        subfolder               = os.path.join(self.Output_Path, current_stage_name)
        data_folder             = os.path.join(subfolder, "data")
        ga_final_merge_folder   = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        convert_gene_map_folder = os.path.join(data_folder, "4_convert_gene_map")
        output_taxa_folder      = os.path.join(data_folder, "3_taxa_table")
        final_folder            = os.path.join(subfolder, "final_results")
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(convert_gene_map_folder)
        self.make_folder(final_folder)
        gene_map_location = os.path.join(ga_final_merge_folder, "gene_map.tsv")
        
        copy_gene_map = ">&2 echo copying gene map | "
        copy_gene_map += "cp " + os.path.join(ga_final_merge_folder, "gene_map.tsv") + " "
        copy_gene_map += convert_gene_map_folder
        
        copy_contig_map = ">&2 echo copying contig map | "
        copy_contig_map += "cp " + os.path.join(output_taxa_folder, "contig_segment_read_map.tsv") + " "
        copy_contig_map += convert_gene_map_folder
        
        convert_gene_map = ">&2 echo converting contig segments to reads | "
        convert_gene_map += self.tool_path_obj.Python + " "
        convert_gene_map += self.tool_path_obj.convert_contig_segments + " "
        convert_gene_map += os.path.join(convert_gene_map_folder, "gene_map.tsv") + " "
        convert_gene_map += os.path.join(convert_gene_map_folder, "contig_segment_read_map.tsv") + " "
        convert_gene_map += os.path.join(final_folder, "final_gene_map.tsv")
        
        return[copy_gene_map, copy_contig_map, convert_gene_map]

    def create_output_clean_ec_report_command(self, current_stage_name, ec_stage):
        subfolder               = os.path.join(self.Output_Path, current_stage_name)
        data_folder             = os.path.join(subfolder, "data")
        ec_folder               = os.path.join(self.Output_Path, ec_stage, "final_results")
        final_gene_map_folder   = os.path.join(data_folder, "4_convert_gene_map")
        clean_ec_folder         = os.path.join(data_folder, "5_cleaned_ec")
        final_folder            = os.path.join(subfolder, "final_results")
        
        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(clean_ec_folder)
        
        clean_ec_all = ">&2 echo Cleaning HQ ECs | "
        clean_ec_all += self.tool_path_obj.Python + " "
        clean_ec_all += self.tool_path_obj.output_filter_ECs + " "
        clean_ec_all += os.path.join(ec_folder, "proteins.ECs_All") + " "
        clean_ec_all += os.path.join(final_folder, "final_gene_map.tsv") + " "
        clean_ec_all += os.path.join(clean_ec_folder, "cleaned_proteins.ECs_All")

        clean_lq_ec = ">&2 echo Cleaning LQ ECs | "
        clean_lq_ec += self.tool_path_obj.Python + " "
        clean_lq_ec += self.tool_path_obj.output_filter_ECs + " "
        clean_lq_ec += os.path.join(ec_folder, "lq_proteins.ECs_All") + " "
        clean_lq_ec += os.path.join(final_folder, "final_gene_map.tsv") + " "
        clean_lq_ec += os.path.join(clean_ec_folder, "cleaned_lq_proteins.ECs_All")
        
        return [clean_ec_all, clean_lq_ec]

        
    def create_output_network_generation_command(self, current_stage_name, ga_final_merge_stage, taxonomic_annotation_stage, enzyme_annotation_stage):
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        ga_final_merge_folder  = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        ta_folder           = os.path.join(self.Output_Path, taxonomic_annotation_stage, "final_results")
        ea_folder           = os.path.join(self.Output_Path, enzyme_annotation_stage, "final_results")
        data_folder         = os.path.join(subfolder, "data")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)
        gene_map_location = os.path.join(final_folder, "final_gene_map.tsv")
        
        network_generation = ">&2 echo Generating RPKM and Cytoscape network | "
        network_generation += self.tool_path_obj.Python + " "
        network_generation += self.tool_path_obj.RPKM + " "
        network_generation += str(self.tool_path_obj.rpkm_cutoff) + " "
        network_generation += "None" + " "
        network_generation += self.tool_path_obj.nodes + " "
        network_generation += self.tool_path_obj.names + " "
        network_generation += gene_map_location + " "
        network_generation += os.path.join(ta_folder, "taxonomic_classifications.tsv") + " "
        network_generation += os.path.join(ea_folder, "proteins.ECs_All") + " "
        network_generation += self.tool_path_obj.show_unclassified + " "
        network_generation += os.path.join(final_folder, "RPKM_table.tsv") + " "
        network_generation += os.path.join(final_folder, "Cytoscape_network.tsv") + " "
        
        flatten_rpkm = ">&2 echo Reformat RPKM for EC heatmap | "
        flatten_rpkm += self.tool_path_obj.Python + " "
        flatten_rpkm += self.tool_path_obj.format_RPKM + " "
        flatten_rpkm += os.path.join(final_folder, "RPKM_table.tsv") + " "
        flatten_rpkm += os.path.join(final_folder, "EC_heatmap_RPKM.tsv")
        
        return [network_generation, flatten_rpkm]
        
    def create_output_unique_hosts_singletons_command(self, current_stage_name, quality_stage, host_stage):
        #only call if we had hosts to filter
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        quality_folder      = os.path.join(self.Output_Path, quality_stage, "final_results")
        host_folder         = os.path.join(self.Output_Path, host_stage, "final_results")
        data_folder         = os.path.join(subfolder, "data")
        unique_hosts_folder = os.path.join(data_folder, "1_unique_hosts")
        full_hosts_folder   = os.path.join(data_folder, "2_full_hosts")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(data_folder)
        self.make_folder(unique_hosts_folder)
        self.make_folder(full_hosts_folder)
        self.make_folder(final_folder)
        
        
        get_unique_host_reads_singletons = ">&2 echo get singleton host reads for stats | "
        get_unique_host_reads_singletons += self.tool_path_obj.Python + " "
        get_unique_host_reads_singletons += self.tool_path_obj.get_unique_host_reads + " "
        get_unique_host_reads_singletons += os.path.join(host_folder, "singletons.fastq") + " "
        get_unique_host_reads_singletons += os.path.join(quality_folder, "singletons.fastq") + " "
        get_unique_host_reads_singletons += os.path.join(unique_hosts_folder, "singleton_hosts.fastq")
        
        
        repop_singletons_hosts = ">&2 echo repopulating singletons hosts | " 
        repop_singletons_hosts += self.tool_path_obj.Python + " "
        repop_singletons_hosts += self.tool_path_obj.duplicate_repopulate + " "
        if(self.read_mode == "single"):
            repop_singletons_hosts += os.path.join(quality_folder, "singletons_hq.fastq") + " "
        else:
            repop_singletons_hosts += os.path.join(quality_folder, "singletons_with_duplicates.fastq") + " "
        repop_singletons_hosts += os.path.join(unique_hosts_folder, "singleton_hosts.fastq") + " "
        repop_singletons_hosts += os.path.join(quality_folder, "singletons_unique.fastq.clstr") + " "
        repop_singletons_hosts += os.path.join(full_hosts_folder, "singletons_full_hosts.fastq")
        
        return [get_unique_host_reads_singletons, repop_singletons_hosts]
        
    def create_output_unique_hosts_pair_1_command(self, current_stage_name, quality_stage, host_stage):
        #only call if we had hosts to filter
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        quality_folder      = os.path.join(self.Output_Path, quality_stage, "final_results")
        host_folder         = os.path.join(self.Output_Path, host_stage, "final_results")
        data_folder         = os.path.join(subfolder, "data")
        unique_hosts_folder = os.path.join(data_folder, "1_unique_hosts")
        full_hosts_folder   = os.path.join(data_folder, "2_full_hosts")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)

        self.make_folder(data_folder)
        self.make_folder(unique_hosts_folder)
        self.make_folder(full_hosts_folder)
        self.make_folder(final_folder)
        
        get_unique_host_reads_pair_1 = ">&2 echo get pair 1 host reads for stats | " 
        get_unique_host_reads_pair_1 += self.tool_path_obj.Python + " "
        get_unique_host_reads_pair_1 += self.tool_path_obj.get_unique_host_reads + " "
        get_unique_host_reads_pair_1 += os.path.join(host_folder, "pair_1.fastq") + " "
        get_unique_host_reads_pair_1 += os.path.join(quality_folder, "pair_1.fastq") + " "
        get_unique_host_reads_pair_1 += os.path.join(unique_hosts_folder, "pair_1_hosts.fastq")
        
        repop_pair_1_hosts = ">&2 echo repopulating pair 1 hosts | " 
        repop_pair_1_hosts += self.tool_path_obj.Python + " "
        repop_pair_1_hosts += self.tool_path_obj.duplicate_repopulate + " "
        repop_pair_1_hosts += os.path.join(quality_folder, "pair_1_match.fastq") + " "
        repop_pair_1_hosts += os.path.join(unique_hosts_folder, "pair_1_hosts.fastq") + " "
        repop_pair_1_hosts += os.path.join(quality_folder, "pair_1_unique.fastq.clstr") + " "
        repop_pair_1_hosts += os.path.join(full_hosts_folder, "pair_1_full_hosts.fastq")
        
        return [get_unique_host_reads_pair_1, repop_pair_1_hosts]
        
    def create_output_unique_hosts_pair_2_command(self, current_stage_name, quality_stage, host_stage):
        #only call if we had hosts to filter
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        quality_folder      = os.path.join(self.Output_Path, quality_stage, "final_results")
        host_folder         = os.path.join(self.Output_Path, host_stage, "final_results")
        data_folder         = os.path.join(subfolder, "data")
        unique_hosts_folder = os.path.join(data_folder, "1_unique_hosts")
        full_hosts_folder   = os.path.join(data_folder, "2_full_hosts")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(data_folder)
        self.make_folder(full_hosts_folder)
        self.make_folder(final_folder)
        
        get_unique_host_reads_pair_2 = ">&2 echo get pair 2 host reads for stats | " 
        get_unique_host_reads_pair_2 += self.tool_path_obj.Python + " "
        get_unique_host_reads_pair_2 += self.tool_path_obj.get_unique_host_reads + " "
        get_unique_host_reads_pair_2 += os.path.join(host_folder, "pair_2.fastq") + " "
        get_unique_host_reads_pair_2 += os.path.join(quality_folder, "pair_2.fastq") + " "
        get_unique_host_reads_pair_2 += os.path.join(unique_hosts_folder, "pair_2_hosts.fastq")
        
        repop_pair_2_hosts = ">&2 echo repopulating pair 2 hosts | " 
        repop_pair_2_hosts += self.tool_path_obj.Python + " "
        repop_pair_2_hosts += self.tool_path_obj.duplicate_repopulate + " "
        repop_pair_2_hosts += os.path.join(quality_folder, "pair_2_match.fastq") + " "
        repop_pair_2_hosts += os.path.join(unique_hosts_folder, "pair_2_hosts.fastq") + " "
        repop_pair_2_hosts += os.path.join(quality_folder, "pair_2_unique.fastq.clstr") + " "
        repop_pair_2_hosts += os.path.join(full_hosts_folder, "pair_2_full_hosts.fastq")
        
        return [get_unique_host_reads_pair_2, repop_pair_2_hosts]
        
        
    def create_output_combine_hosts_command(self, current_stage_name):
        #only call if we had hosts to filter, and run it after the host regen is complete.
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        full_hosts_folder   = os.path.join(data_folder, "2_full_hosts")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(full_hosts_folder)
        
        combine_hosts = ">&2 echo combining hosts | " 
        combine_hosts += "cat" + " "
        combine_hosts += os.path.join(full_hosts_folder, "singletons_full_hosts.fastq") + " "
        if(self.read_mode == "paired"):
            combine_hosts += os.path.join(full_hosts_folder, "pair_1_full_hosts.fastq") + " "
            combine_hosts += os.path.join(full_hosts_folder, "pair_2_full_hosts.fastq") + " "
        combine_hosts += ">" + " "
        combine_hosts += os.path.join(full_hosts_folder, "combined_hosts.fastq")
        
        
        return [combine_hosts]
        
        
    def create_output_per_read_scores_command(self, current_stage_name, quality_stage):
        #only call if we had hosts to filter, and run it after the host regen is complete.
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        quality_folder      = os.path.join(self.Output_Path, quality_stage, "final_results")
        data_folder         = os.path.join(subfolder, "data")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)
        
        per_read_scores = ">&2 echo collecting per-read quality | " 
        per_read_scores += self.tool_path_obj.Python + " "
        per_read_scores += self.tool_path_obj.read_quality_metrics + " "
        if(self.read_mode == "single"):
            per_read_scores += "single" + " "
            per_read_scores += self.sequence_single + " "
            per_read_scores += os.path.join(quality_folder, "singletons_hq.fastq") + " "
            per_read_scores += os.path.join(final_folder)
            
        elif(self.read_mode == "paired"):
            per_read_scores += "paired" + " " 
            per_read_scores += self.sequence_path_1 + " "
            per_read_scores += self.sequence_path_2 + " "
            per_read_scores += os.path.join(quality_folder, "pair_1_match.fastq") + " "
            per_read_scores += os.path.join(quality_folder, "pair_2_match.fastq") + " "
            per_read_scores += os.path.join(quality_folder, "singletons_with_duplicates.fastq") + " "
            per_read_scores += os.path.join(final_folder)
            
        return [per_read_scores]
        
        
        
        
    def create_output_contig_stats_command(self, current_stage_name, contig_stage):
        #only call if we had hosts to filter, and run it after the host regen is complete.
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        contig_folder       = os.path.join(self.Output_Path, contig_stage, "final_results")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)
        
        contig_stats = ">&2 echo collecting contig stats | " 
        contig_stats += self.tool_path_obj.Python + " "
        contig_stats += self.tool_path_obj.contig_stats + " "
        contig_stats += os.path.join(contig_folder, "contigs.fasta") + " "
        contig_stats += os.path.join(final_folder, "contig_stats.txt")
        
        return [contig_stats]
        
    def create_output_EC_heatmap_command(self, current_stage_name):
        #only call if we had hosts to filter, and run it after the host regen is complete.
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(final_folder)
        
        EC_heatmap = ">&2 echo forming EC heatmap | "
        EC_heatmap += self.tool_path_obj.Python + " "
        EC_heatmap += self.tool_path_obj.ec_heatmap + " "
        EC_heatmap += self.tool_path_obj.EC_pathway + " "
        EC_heatmap += os.path.join(final_folder, "EC_heatmap_RPKM.tsv") + " "
        EC_heatmap += self.tool_path_obj.path_to_superpath + " "
        EC_heatmap += final_folder
        
        return [EC_heatmap]
        
        
        
    def create_output_read_count_command(self, current_stage_name, quality_stage, repopulation_stage, ga_final_merge_stage, enzyme_annotation_stage):
        #only call if we had hosts to filter, and run it after the host regen is complete.
        subfolder           = os.path.join(self.Output_Path, current_stage_name)
        data_folder         = os.path.join(subfolder, "data")
        quality_folder      = os.path.join(self.Output_Path, quality_stage, "final_results")
        repopulation_folder = os.path.join(self.Output_Path, repopulation_stage, "final_results")
        final_merge_folder  = os.path.join(self.Output_Path, ga_final_merge_stage, "final_results")
        ea_folder           = os.path.join(self.Output_Path, enzyme_annotation_stage, "final_results")
        full_hosts_folder   = os.path.join(data_folder, "2_full_hosts")
        final_folder        = os.path.join(subfolder, "final_results")

        self.make_folder(subfolder)
        self.make_folder(data_folder)
        self.make_folder(full_hosts_folder)
        self.make_folder(final_folder)
        gene_map_location = os.path.join(final_folder, "final_gene_map.tsv")
        
        read_counts = ">&2 echo generating read count table | "
        read_counts += self.tool_path_obj.Python + " "
        read_counts += self.tool_path_obj.read_count + " "
        if self.read_mode == "single":
            read_counts += self.sequence_single + " "
            read_counts += os.path.join(quality_folder, "singletons_hq.fastq") + " "
            read_counts += os.path.join(repopulation_folder, "singletons_rRNA.fastq") + " "
            read_counts += os.path.join(repopulation_folder, "singletons.fastq") + " "
        elif self.read_mode == "paired":
            read_counts += self.sequence_path_1 + " "
            read_counts += os.path.join(quality_folder, "singletons_with_duplicates.fastq") + ","
            read_counts += os.path.join(quality_folder, "pair_1_match.fastq") + " "
            read_counts += os.path.join(repopulation_folder, "singletons_rRNA.fastq") + ","
            read_counts += os.path.join(repopulation_folder, "pair_1_rRNA.fastq") + " "
            read_counts += os.path.join(repopulation_folder, "singletons.fastq") + ","
            read_counts += os.path.join(repopulation_folder, "pair_1.fastq") + " "
        read_counts += gene_map_location + " "
        read_counts += os.path.join(ea_folder, "proteins.ECs_All") + " "
        if(self.no_host_flag):
            read_counts += "no_host" + " "
        else:
            read_counts += os.path.join(full_hosts_folder, "combined_hosts.fastq") + " "
        read_counts += os.path.join(final_folder, "read_count.tsv")    
        
        return [read_counts]