#!/usr/bin/env python

# Now with some commenting!
# CHANGES:
# - added .strip("\n") to extracting from the gene2read_file
# - fixed sort function to return float
# - reversed the sort direction to get largest scores at top
# - pulled gene_map() out of the readtype loop
# - rewrote gene_map()
# - removed checks to see if contig/read was already assigned to same gene (shouldn't happen)
# - removed check to see if query=read was already mapped by DMD (shouldn't happen)
# - multiplied align_len*3 to convert aa->nt
# - changed align_len to float(align_len) (to make sure it's a number)
# - stores aligned proteins in new dict prot2read_map, instead of gene2read_map:
#   readability esp. during WRITE OUTPUT: BWA&BLAT&DMD-aligned;
#   also only check new DMD alignements against protein list for duplicates
# - paired-end DMD outputs are combined and analyzed at the same time
# - fixed WRITE OUTPUT: non-BWA&BLAT&DMD-aligned: changed "mapped_reads.add" to "break"

# NOTE:
# - Filenames for unmerged paired-end reads must be specified last.
# - Sometimes reads will be matched to multiple genes. This occurs between
#   BLAT contig alignement and DMD contig alignment.
# - DMDpp only takes the read<->gene match with the top score. For duplicate
#   top scores, it only takes the one that shows up first in the initial sort.
# - The paired-end DMD outputs are combined and analyzed at the same time, in order to
#   rank the matches between different ends of the same read, and not double count that read.
# - Sometimes a read is aligned via multiple contigs and annoteted only according
#   to the best matched contig only. Theoretically, this breaks up the other contigs.

#OTHER NOTES: Feb 27, 2019
# - this is a messy Piece-of-shit code that needs to be written without those dumb import loops.

import os
import os.path
import sys
from collections import Counter
from collections import defaultdict
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from datetime import datetime as dt
from shutil import copyfile
import pandas as pd
import itertools


#####################################
# FUNCTIONS:
def check_file_safety(file_name):
    if(os.path.exists(file_name)):
        if(os.path.getsize(file_name) == 0):
            #copyfile(gene2read_file, new_gene2read_file)
            print(file_name, "is unsafe.  skipping")
            return False
            #sys.exit(DMD_tab_file_1 + " -> DMD tab file 1 is empty.  aborting")
        else:
            print(file_name, "exists and is safe")
            return True
    else:
        #sys.exit(DMD_tab_file_1 + " -> DMD tab file 1 is missing.  aborting")
        print(file_name, "is missing. skipping")
        return False



# read .dmdout file and acquire read length:
def get_dmd_hit_details(dmd_out_file, seqrec):                          
#   List of lists [dmdout info, read length]
    # get info from .blatout file:
    print (dt.today(), 'Reading ' + str(os.path.basename(dmd_out_file)) + '.')
    with open(dmd_out_file,"r") as dmd_out:
        hits= []                                        # List of lists containing .blatout fields.
        for line in dmd_out:                            # In the .dmdout file:
            if len(line)>=2:                            # If length of line >= 2,
                info_list= line.strip("\n").split("\t") #  make a list from .dmdout tab-delimited fields,
                read_id = info_list[0]                     #  get the queryID= contig/readID, -> 
                info_list.append(len(seqrec[read_id].seq))#  add query length (int) to end of list,
                hits.append(info_list)                  #  and append the list to the hits list.
    print(dt.today(), "finished read-aligning")
    return hits

# sort function: sort by score:
# (12th field of the .dmdout file)
def sortbyscore(line):
    return line[11]


def initial_dmdout_filter(hits):
    #sorts and sifts out stuff from the dmdout
    sorted_hits = sorted(hits, key=sortbyscore, reverse=True)     # sort alignment list by high score:
    del hits
        
    # DMD threshold:
    identity_cutoff= 85
    length_cutoff= 0.65
    score_cutoff= 60
    
    # tracking DMD-assigned & unassigned:
    #query2prot_map = defaultdict(set)        # Dict of DMD-aligned contig/readID<->protID(s).
    #queryIScontig = {}                       # Dict of DMD-aligned contig/readID<->contig? (True/False).
    unmapped = set()                         # Set of unmapped contig/readIDs.
    
    query_details_dict = dict() #dict of dict: level 1: query.  level 2: contig-bool, proteins
    
    # loop through sorted DMD-aligned reads/contigs:
    for line in sorted_hits:
        inner_dict = dict() 
        
        # extract & store data:
        query = line[0]                      # query= contig/readID
        db_match = line[1]                   # proteinID
        seq_identity = float(line[2])        # sequence identity
        align_len = 3*int(line[3])           # alignment length (aa->nt)
        score = float(line[11])              # score
        seq_len = int(line[12])              # query sequence length
        
        # is this alignment the highest-score match for that query?
        print("---------------------------------------------")
        #if query in query2prot_map:         # If alignment previously found for this contig/read,
        if query in query_details_dict:
            print(dt.today(), "read ID found:", query, "skipping")
            continue                        # skip to next qurey as this alignment will have a lower score,
        
            
        # is query a contig?:
        contig_flag = False 
        if query in contig2read_map:        # If query is found in contig list,
            contig_flag = True                    #  then mark as contig,
        
        # does query alignment meet threshold?: # (identity, length, score):
        if seq_identity<=identity_cutoff or align_len<=seq_len*length_cutoff or score<=score_cutoff:
            unmapped.add(query)             # if threshold is failed, add to unmapped set and
            continue                        # skip to the next query.
   
        
        # store info for queries that remain:
        #queryIScontig[query]= contig_flag        # Store contig (T/F) info.
        #query2prot_map[query].add(db_match) # Collect all aligned prot for contig/read;
        inner_dict["is_contig"] = contig_flag
        inner_dict["protein"] = db_match
        
        query_details_dict[query] = inner_dict
        
        print(dt.today(), "new read ID:", query, "adding")
        if(contig_flag):
            print(dt.today(), "it's also part of a contig")
            
    print(dt.today(), "done initial filtering")        
    return unmapped, query_details_dict #query2prot_map, queryIScontig
    
# def form_prot_map_inner(prot_map_chunk, read_idIScontig):
    # #the inner stage, this part works in parallel
    # contigread_inmapped= 0
    # contigread_inmapped_inprot= 0
    # contigread_inprot= 0
    # read_inmapped= 0
    # read_inmapped_inprot= 0
    # read_inprot= 0
 
    # #print(dt.today(), "sifting through read-ID -> protein map")
    # # FINAL remaining DMD-aligned queries:
    # for read_id in prot_map_chunk:         
    
        # db_match = list(prot_map_chunk[read_id])[0]        # geneID (pull out of 1-element set)
        # contig_flag = read_idIScontig[read_id]                    # contig?

        # # RECORD alignment:
        # if contig_flag:                                      
            # #print(dt.today(), read_id, "is part of a contig")
            # for read in contig2read_map[read_id]:    
                # if read in mapped_reads:                # (Track how many contig reads have already been mapped by DMD---i.e., through other contigs---
                    # contigread_inmapped+= 1             
                    # #print(dt.today(), read_id, "is also mapped")
                    # if read in prot2read_map[db_match]: #  and how many of those were already assigned to this particular prot---i.e., contigs aligned to same prot.)
                        # contigread_inmapped_inprot+= 1  
                        
                # elif read in prot2read_map[db_match]:   # (Check to see if any of the contig reads are already assigned to this particular prot, but not by DMD.)
                    # contigread_inprot+= 1              
                    
                # if read not in mapped_reads:            #  if not already assigned by DMD to a diff prot***, then and append their readIDs to aligned prot<->read dict, and mark them as assigned by DMD.
                    # #print(dt.today(), "contig:", read_id, ":", read, "read part of contig, but not mapped yet.  adding contig-read")
                    # prot2read_map[db_match].append(read) 
                    # mapped_reads.add(read)                
                
        
        # else:
            # #print(dt.today(), read_id, "is not a contig")
            # # DEBUG:
            # if read_id in mapped_reads:                   # (Check to see if the read has already been mapped
                # read_inmapped+= 1                       #  by DMD---it shouldn't be---and
                # if read_id in prot2read_map[db_match]:    #  and to the same prot, for that matter.
                    # read_inmapped_inprot+= 1
            # elif read_id in prot2read_map[db_match]:      # (Check to see if the read is already assigned to this
                # read_inprot+= 1                         #  particular prot, but not by DMD---it shouldn't be.)

            # prot2read_map[db_match].append(read_id)       #  append its readID to aligned prot<->read dict,
            # mapped_reads.add(read_id)                     #  and mark it as assigned by DMD.
            # #print(dt.today(), "added to mapped reads")

# add DMD-aligned reads that meet threshold
# to the aligned gene/protID<->readID(s) dict:
def form_prot_map(hits, mapped_reads, contig2read_map, prot2read_map): 
    #contig2read map is external.  should contain upstream runs' contigs
    #prot2read map is external.  should contain prior calls' proteins
    
    unmapped, query_details_dict = initial_dmdout_filter(hits) #unmapped, query2prot_map, queryIScontig = initial_dmdout_filter(hits)
    # EXPAND HERE to deal with multiple high-score genes for a read.
    print(dt.today(), "finished initial sorting")  
    
    #checking
    if(len(prot2read_map) == 0):
        print(dt.today(), "prot2read map is empty")
    else:
        print(dt.today(), "prot2read map is not empty")
        
    if(len(contig2read_map) == 0):
        print(dt.today(), "contig2read map is empty")
    else:
        print(dt.today(), "contig2read map not empty")
        

      
    # DEBUG:
    contigread_inmapped = 0
    contigread_inmapped_inprot = 0
    contigread_inprot = 0
    read_inmapped = 0
    read_inmapped_inprot = 0
    read_inprot = 0
 
    query_keys = list(query_details_dict.keys())#query2prot_map.keys())
    print(dt.today(), "read ID 2 prot map keys:", len(query_keys))
 
    print(dt.today(), "sifting through read-ID -> protein map")
    # FINAL remaining DMD-aligned queries:
    #for query in query2prot_map:                        # contig_ID or read_ID.  DIAMOND spits out queries.
    for query in query_keys:
        db_match = query_details_dict[query]["protein"]#list(query2prot_map[query])[0]        # geneID (pull out of 1-element set)
        contig_flag = query_details_dict[query]["is_contig"]#queryIScontig[query]                    # contig?

        # RECORD alignment:
        if contig_flag:                                      
            #print(dt.today(), query, "is part of a contig")
            for read in contig2read_map[query]:    
                if read in mapped_reads:                # (Track how many contig reads have already been mapped by DMD---i.e., through other contigs---
                    contigread_inmapped+= 1             
                    #print(dt.today(), query, "is also mapped")
                    if read in prot2read_map[db_match]: #  and how many of those were already assigned to this particular prot---i.e., contigs aligned to same prot.)
                        contigread_inmapped_inprot+= 1  
                        
                elif read in prot2read_map[db_match]:   # (Check to see if any of the contig reads are already assigned to this particular prot, but not by DMD.)
                    contigread_inprot+= 1              
                    
                if read not in mapped_reads:            #  if not already assigned by DMD to a diff prot***, then and append their readIDs to aligned prot<->read dict, and mark them as assigned by DMD.
                    #print(dt.today(), "contig:", query, ":", read, "read part of contig, but not mapped yet.  adding contig-read")
                    prot2read_map[db_match].append(read) 
                    mapped_reads.add(read)                
                
        
        else:
            #print(dt.today(), query, "is not a contig")
            # DEBUG:
            if query in mapped_reads:                   # (Check to see if the read has already been mapped
                read_inmapped+= 1                       #  by DMD---it shouldn't be---and
                if query in prot2read_map[db_match]:    #  and to the same prot, for that matter.
                    read_inmapped_inprot+= 1
            elif query in prot2read_map[db_match]:      # (Check to see if the read is already assigned to this
                read_inprot+= 1                         #  particular prot, but not by DMD---it shouldn't be.)

            prot2read_map[db_match].append(query)       #  append its readID to aligned prot<->read dict,
            mapped_reads.add(query)                     #  and mark it as assigned by DMD.
            #print(dt.today(), "added to mapped reads")
        
        #print("========================================================")
        # *** This deals with reads that show up in multiple contigs.
        # Just use the read alignment from the contig that had the best alignment score.
        # This could result in "broken" contigs...

    # DEBUG (for this datatype):
    print ('no. contig reads already mapped by DMD= ' + str(contigread_inmapped))
    print ('no. contig reads mapped by DMD to same prot= ' + str(contigread_inmapped_inprot))
    print ('no. contig reads mapped by NOT DMD to same prot= ' + str(contigread_inprot) + ' (should be 0)')
    print ('no. reads already mapped by DMD= ' + str(read_inmapped) + ' (should be 0)')
    print ('no. reads already mapped by DMD to same prot= ' + str(read_inmapped_inprot) + ' (should be 0)')
    print ('no. reads already mapped by NOT DMD to same prot= ' + str(read_inprot) + ' (should be 0)')

    # Remove contigs/reads previously added to the unmapped set but later found to have a mapping:
    # This prevents re-annotation by a later program.
    # Such queries end up in the unmapped set when they DMD-aligned to multiple prots, where one
    # alignment is recorded, while the other alignments fail the "on-the-fly" alignment-threshold filter.
    print ('umapped no. (before double-checking mapped set)= ' + str(len(unmapped)))
    #for query in query2prot_map:                        # Take all contigs/reads to be mapped and
    for query in query_keys:
        try:                                            #  if they exist in the unmapped set, then
            unmapped.remove(query)                      #  remove them from the unmapped set.
        except:
            pass
    print ('umapped no. (after double-checking mapped set)= ' + str(len(unmapped)))

    # return unmapped set:
    return unmapped

# WRITE OUTPUT: rewrite gene<->read map file to include DMD-aligned:
# [BWA&BLAT&DMD-aligned geneID, length, #reads, readIDs ...]
def write_proteins_genemap(gene_seqs, gene2read_map, mapped_reads, prot2read_map, Prot_DB, prot_file, new_gene2read_file):
    reads_count= 0
    proteins= []
    with open(new_gene2read_file,"w") as out_map:               # Delete old gene2read_file and write a new one.
    
        # write genes:
        for gene in gene2read_map:                          # Take each BWA&BLAT-aligned gene and
            out_map.write(gene + "\t" + gene_len[gene] + "\t" + str(len(gene2read_map[gene])))
                                                            #  write [aligned geneID, length (in nt), #reads],
            for read in gene2read_map[gene]:
                out_map.write("\t" + read.strip("\n"))      #  [readIDs ...],
            else:
                out_map.write("\n")                         #  and a new line character.
    
        # write proteins:
        for record in SeqIO.parse(Prot_DB,"fasta"):         # Loop through SeqRec of all prot in PROTdb:
                                                            #  (PROTdb is needed to get the aa sequence.)
            if record.id in prot2read_map:                  #  If PROTdb prot is one of the matched proteins,
                proteins.append(record)                     #  append the SeqRec to proteins list (for next file), and
                out_map.write(record.id + "\t" + str(len(record.seq)*3) + "\t" + str(len(prot2read_map[record.id])))
                                                            #  write [aligned protID, length (in nt), #reads, ...],
                for read in prot2read_map[record.id]:
                    out_map.write("\t" + read.strip("\n"))  #  [readIDs ...],
                    reads_count+= 1
                else:
                    out_map.write("\n")                     #  and a new line character.
    
    # WRITE OUTPUT: BWA&BLAT&DMD-aligned gene/protIDs and aa seqs
    # (.faa; fasta-format):
    genes_trans= []
    for gene in gene_seqs:                                  # Take each BWA&BLAT-aligned genes
        try:
            genes_trans.append(SeqRecord(seq= gene_seqs[gene].seq.translate(stop_symbol=""), id= gene_seqs[gene].id, description= gene_seqs[gene].description))
                                                            #  and translate its SeqRecord sequence to aa.
        except:
            pass
    no_write = True
    if(~no_write):
        with open(prot_file,"w") as out_prot:
            SeqIO.write(genes_trans, out_prot, "fasta")         # Write aligned gene aa seqs
            SeqIO.write(proteins, out_prot, "fasta")            #  and aligned proteins aa seqs.
    
    else:
        print(dt.today(), "IN TRIAGE-MODE: not writing FASTAs")
    # print DMD stats:
    print (str(reads_count) + ' reads were mapped with Diamond.')
    print ('Reads mapped to ' + str(len(proteins)) + ' proteins.')
    
    
def filter_consumed_reads(read_file, DMD_tab_file, output_file, mapped_reads, prev_mapping_count, contig2read_map, prot2read_map):    
    # check number of readtype sets (file inputs)
    read_sets = int((len(sys.argv)-7)/3) 
    if (len(sys.argv)-7) % 3 != 0:
        sys.exit('Incorrect number of readtype sets: ' + str(len(sys.argv)))
    
    # process DIAMOND output: # readtype sets: contigs, merged:
    read_seqs= SeqIO.index(read_file, os.path.splitext(read_file)[1][1:]) #import reads (index.   key: read_id -> val: seq)
    if(check_file_safety(DMD_tab_file)):
        print(dt.today(), DMD_tab_file, "is ok")
    else:
        print(dt.today(), DMD_tab_file, "is not ok.  killing program")
        sys.exit()

    # read DMD output & get read/contig lengths:
    DMD_hits = get_dmd_hit_details(DMD_tab_file, read_seqs)     # Store info in DMD_hits (list of lists).

    # process DMD-aligned reads:
    
    unmapped_reads = form_prot_map(DMD_hits, mapped_reads, contig2read_map, prot2read_map)    # Store DMD-aligned contigs/reads in prot2read_map
    
    #sanity-check:
    unique_reads = set()
    read_count = 0
    for key in prot2read_map:
        prot_reads_list = prot2read_map[key]
        for item in prot_reads_list:
            read_count += 1
            unique_reads.add(item)
    print(dt.today(), "number of unique reads:", len(unique_reads))
    print(dt.today(), "number of counted reads:", read_count)
    
    if(len(unique_reads) != read_count):
        print(dt.today(), "failed sanity check:", read_file)
        sys.exit()
        
        
                                                        #  (aligned protID<->readID(s) dict),
                                                        #  and return a set of failed mapping readIDs.
    # add reads never mapped by DMD in the
    # first place to the unmapped set:
    unmapped_len_before= len(unmapped_reads)            # DEBUG
    for read in read_seqs:                              # Take all non-BWA&BLAT-aligned contigs/reads (input to DMD)
        if read not in mapped_reads:                    #  that are still unmapped and
            unmapped_reads.add(read)                    #  add them to the unmapped_reads set (won't add duplicates).

    print ('no. additional contigs/reads completely unmapped by DMD= ' + str(len(unmapped_reads)-unmapped_len_before))

    # WRITE OUTPUT: non-BWA&BLAT&DMD-aligned contig/readIDs:
    # and seqs (.fasta)
    no_write = True
    if(~no_write):
        print(dt.today(), "writing fasta")
        unmapped_seqs= []                                   # Initialize list of SeqRecords.
        for read in unmapped_reads:                         # Put corresponding SeqRecords for unmapped_reads
            unmapped_seqs.append(read_seqs[read])           #  into unmapped_seqs
        with open(output_file,"w") as outfile:
            SeqIO.write(unmapped_seqs, outfile, "fasta")    #  and write it to file.
    else:
        print(dt.today(), "IN TRIAGE-MODE: skipping the leftover seq writing.")
    # print no. aligned reads from current readtype set:
    print (str(len(mapped_reads)-prev_mapping_count) + ' additional reads were mapped from ' + os.path.basename(read_file) + '\n')
    prev_mapping_count= len(mapped_reads)
        
def construct_contig2read_map(contig2read_file):
    # make dict of contigID<->readsID(s):
    contig2read_map= {}                                 #Input: key->contig | val->reads
    with open(contig2read_file,"r") as mapping:
        for line in mapping:
            if len(line)>5:                             # line starts with 'NODE_'
                entry= line.strip("\n").split("\t")     # break tab-separated into list
                contig2read_map[entry[0]]= entry[2:]    # key=contigID, value=list of readID(s)
    return contig2read_map


#####################################
if __name__ == "__main__":

    Prot_DB             = sys.argv[1]   # INPUT: AA db used for DIAMOND alignement
    contig2read_file    = sys.argv[2]   # INPUT: [contigID, #reads, readIDs ...]
    gene2read_file      = sys.argv[3]   # INPUT: [BWA&BLAT-aligned geneID, length, #reads, readIDs ...]
    new_gene2read_file  = sys.argv[4]   # OUTPUT: [BWA&BLAT&DMD-aligned gene/protID, length, #reads, readIDs ...]
    gene_file           = sys.argv[5]   # INPUT: BWA&BLAT-aligned geneIDs and nt seqs (.fna; fasta-format)
    prot_file           = sys.argv[6]   # OUTPUT: BWA&BLAT&DMD-aligned gene/protIDs and aa seqs (.faa; fasta-format)
    
    contigs_reads_in    = sys.argv[7]
    contigs_dmd_out     = sys.argv[8]
    contigs_reads_out   = sys.argv[9]
    
    singletons_reads_in = sys.argv[10]
    singletons_dmd_out  = sys.argv[11]
    singletons_reads_out= sys.argv[12]
    
    #check file integrity:
    contigs_safe = check_file_safety(contigs_reads_in) and  check_file_safety(contigs_dmd_out) and check_file_safety(contigs_reads_out)
    singletons_safe = check_file_safety(singletons_reads_in) and check_file_safety(singletons_dmd_out) and check_file_safety(singletons_reads_out)
    
    pair_1_safe = False
    pair_2_safe = False
    operating_mode = "single"
    if(len(sys.argv) == 19):
        operating_mode = "paired"
        pair_1_reads_in = sys.argv[13]
        pair_1_dmd_out  = sys.argv[14]
        pair_1_reads_out= sys.argv[15]
        
        pair_2_reads_in = sys.argv[16]
        pair_2_dmd_out  = sys.argv[17]
        pair_2_reads_out= sys.argv[18]
        
        pair_1_safe = check_file_safety(pair_1_reads_in) and check_file_safety(pair_1_dmd_out) and check_file_safety(pair_1_reads_out)
        pair_2_safe = check_file_safety(pair_2_reads_in) and check_file_safety(pair_2_dmd_out) and check_file_safety(pair_2_reads_out)
        
    print(dt.today(), "OPERATING MODE:", operating_mode)
    
    #"global" vars
    contig2read_map = construct_contig2read_map(contig2read_file)   #Input: key->contig | val->reads
    BWABLATreads = []                                    
    gene2read_map = {}                                   #Input: key->geneID | val->reads
    gene_len = {}
    mapped_reads = set()                                 # tracks DMD-assigned reads
    prot2read_map = defaultdict(list)                    # dict of DMD-aligned protID<->readID(s) #  key=protID, value=list of readID(s)
    prev_mapping_count = 0
    
    
    
    # make dict of BWA&BLAT-aligned geneID<->readID(s):
    with open(gene2read_file,"r") as mapping:
        for line in mapping:
            if len(line)>5:                             # line at least 5 characeters?
                entry= line.strip("\n").split("\t")
                gene2read_map[entry[0]]= entry[3:]      # key=geneID, value=list of readID(s) (using [:] syntax ensures a list, even if one ele)
                gene_len[entry[0]]= entry[1]            # key=geneID, value=gene length; to avoid recalc later
                BWABLATreads.extend(entry[3:])          # DEBUG
    
    
    # make dict of BWA&BLAT-aligned geneID<->seq:
    gene_seqs= SeqIO.index(gene_file,"fasta")           # key=geneID, value=SeqRecord
    
    
    if len(set(BWABLATreads))==len(BWABLATreads):
        print ('BWA&/orBLAT-aligned reads are all unique.\n')
    else:
        print ('There are repeating BWA&/orBLAT-aligned reads:')
        print ('no. unique reads= ' + str(len(set(BWABLATreads))))
        print ('no. total reads= ' + str(len(BWABLATreads)) + '\n')
    BWABLATreads_count= Counter(BWABLATreads)           # dict of read<->no. of contigs
    # Write the outputs that don't actually need the dmdout crap
    
#    for x in range (0, 2):
#        read_file = sys.argv[3*x+7]
#        DMD_tab_file = sys.argv[3*x+8]
#        output_file = sys.argv[3*x+9]
#        
#        filter_consumed_reads(read_file, DMD_tab_file, output_file, mapped_reads, prev_mapping_count, contig2read_map, prot2read_map)
    filter_consumed_reads(contigs_reads_in, contigs_dmd_out, contigs_reads_out, mapped_reads, prev_mapping_count, contig2read_map, prot2read_map)
    filter_consumed_reads(singletons_reads_in, singletons_dmd_out, singletons_reads_out, mapped_reads, prev_mapping_count, contig2read_map, prot2read_map)
    if(operating_mode == "paired"):
        filter_consumed_reads(pair_1_reads_in, pair_1_dmd_out, pair_1_reads_out, mapped_reads, prev_mapping_count, contig2read_map, prot2read_map)
        filter_consumed_reads(pair_2_reads_in, pair_2_dmd_out, pair_2_reads_out, mapped_reads, prev_mapping_count, contig2read_map, prot2read_map)
    
    # check number of readtype sets (file inputs)
    read_sets = int((len(sys.argv)-7)/3) 
    if (len(sys.argv)-7) % 3 != 0:
        print(dt.today(), "incorrect number of read sets, but we'll still write the gene map")
        write_proteins_genemap(gene_seqs, gene2read_map, mapped_reads, prot2read_map, Prot_DB, prot_file, new_gene2read_file)
        sys.exit('Incorrect number of readtype sets: ' + str(len(sys.argv)))

    # process DMD output:
    # readtype sets: unmerged1, unmerged2
    if read_sets==4:
        
        # unmerged1:
        x= 2
        read_file_1= sys.argv[3*x+7]
        read_seqs_1= SeqIO.index(read_file_1, os.path.splitext(read_file_1)[1][1:])
        DMD_tab_file_1= sys.argv[3*x+8]
        if(check_file_safety(DMD_tab_file_1)):    
            output_file_1= sys.argv[3*x+9]
            DMD_hits_1= get_dmd_hit_details(DMD_tab_file_1, read_seqs_1)   # Store info in DMD_hits_1 (list of lists).
        
            # unmerged2:
            x= 3
            read_file_2= sys.argv[3*x+7]
            read_seqs_2= SeqIO.index(read_file_2, os.path.splitext(read_file_2)[1][1:])
            DMD_tab_file_2= sys.argv[3*x+8]
            if(check_file_safety(DMD_tab_file_2)):
                output_file_2= sys.argv[3*x+9]
                DMD_hits_2= get_dmd_hit_details(DMD_tab_file_2, read_seqs_2)   # Store info in DMD_hits_2 (list of lists).
            
                # process DMD-aligned reads together:
                DMD_hits= DMD_hits_1+DMD_hits_2                     # Concatenate DMD info lists,
                unmapped_reads= prot_map(DMD_hits, mapped_reads)                  #  add DMD-aligned contigs/reads to gene2read_map
                                                                    #  and return a set of failed mapping readIDs.
                # add reads never mapped by DMD in the
                # first place to the unmapped set:
                unmapped_len_before= len(unmapped_reads)
                for read in read_seqs_1:
                    if read not in mapped_reads:
                        unmapped_reads.add(read)
                print ('(1st paired end) no. additional contigs/reads completely unmapped by DMD= ' + str(len(unmapped_reads)-unmapped_len_before))
            
                # add reads never mapped by DMD in the
                # first place to the unmapped set:
                unmapped_len_before= len(unmapped_reads)
                for read in read_seqs_2:
                    if read not in mapped_reads:
                        unmapped_reads.add(read)
                print ('(2nd paired end) no. additional contigs/reads completely unmapped by DMD= ' + str(len(unmapped_reads)-unmapped_len_before) + ' (should be 0)')
            
                # WRITE unmerged1 OUTPUT: non-BWA&BLAT&DMD-aligned:
                unmapped_seqs= []
                for read in unmapped_reads:
                    read_key = read
                    #if(not read.startswith("@")):
                    #    read_key = "@" + read
                    if(read_key in read_seqs_1):
                        unmapped_seqs.append(read_seqs_1[read_key])
                    else:
                        print(read_key,"from",DMD_tab_file_1, DMD_tab_file_2,   "not found in:", read_file_1)
                with open(output_file_1,"w") as outfile:
                    SeqIO.write(unmapped_seqs, outfile, "fasta")
            
                # WRITE unmerged2 OUTPUT: non-BWA&BLAT&DMD-aligned:
                unmapped_seqs= []
                for read in unmapped_reads:
                    read_key = read
                    #if(not read.startswith("@")):
                    #    read_key = "@" + read
                    if(read_key in read_seqs_2):    
                        unmapped_seqs.append(read_seqs_2[read_key])
                    
                    else:
                        print(read_key,"from",DMD_tab_file_1, DMD_tab_file_2,   "not found in:", read_file_1)
                with open(output_file_2,"w") as outfile:
                    SeqIO.write(unmapped_seqs, outfile, "fasta")
            
                # print no. aligned reads from current readtype set:
                print (str(len(mapped_reads)-prev_mapping_count) + ' additional reads were mapped from ' + os.path.basename(read_file_1))
                print ('  and ' + os.path.basename(read_file_2) + '\n')
                prev_mapping_count= len(mapped_reads)
                
                print(dt.today(), "everything is fine.  writing gene map")
                write_proteins_genemap(gene_seqs, gene2read_map, mapped_reads, prot2read_map, Prot_DB, prot_file, new_gene2read_file)
            
            else:
                print(dt.today(), "dmdout 2 file is missing or has an error.  we'll skip to writing the gene map")
                write_proteins_genemap(gene_seqs, gene2read_map, mapped_reads, prot2read_map, Prot_DB, prot_file, new_gene2read_file)
                
        else:
            print(dt.today(), "dmdout 1 file is missing or has an error. we'll skip to writing the gene map")
            write_proteins_genemap(gene_seqs, gene2read_map, mapped_reads, prot2read_map, Prot_DB, prot_file, new_gene2read_file)
    else:
        print(dt.today(), "not enough read sets.  likely this sample doesn't contain pair 1 or pair 1 data.")  
        print(dt.today(), "we'll write the map anyway.  It should contain the updated data.")
        write_proteins_genemap(gene_seqs, gene2read_map, mapped_reads, prot2read_map, Prot_DB, prot_file, new_gene2read_file)