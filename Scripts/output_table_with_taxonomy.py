#!/usr/bin/env python

import sys

nodes = sys.argv[1]         #IN: nodes.dmp
gene2read = sys.argv[2]     #IN: the gene_map (genes to reads)
read2taxid = sys.argv[3]    #IN: reads to taxid (taxonomic classifications)
gene2EC = sys.argv[4]       #IN: proteins.EC all
read2taxonomy = sys.argv[5] #IN: constrain classification.tsv
RPKM = sys.argv[6]          #OUT: rpkm table
Cytoscape = sys.argv[7]     #OUT cytoscape table


Rank = ["Eukaryota",
    "Archaea",
    "Bacteria",
    "Bacteroidetes",
    "Actinobacteria",
    "Proteobacteria",
    "Gammaproteobacteria",
    "Betaproteobacteria",
    "Alphaproteobacteria",
    "Firmicutes",
    "Bacilli",
    "Clostridia",
    "Lachnospiraceae",
    "Eubacteriaceae",
    "Ruminococcaceae",
    "Clostridiaceae",
    "Oscillospiraceae",
    ]

Rank_id = ["2759",
    "2157",
    "2",
    "976",
    "201174",
    "1224",
    "1236",
    "28216",
    "28211",
    "1239",
    "91061",
    "186801",
    "186803",
    "186806",
    "541000",
    "31979",
    "216572",
    ]

Rank_colour = ["#FFA500",
    "#C0C0C0",
    "#EDF252",
    "#0000FF",
    "#FF00FF",
    "#2C94DE",
    "#ED4734",
    "#00FFFF",
    "#FFCCFF",
    "#34C400",
    "#A52A2A",
    "#663366",
    "#F0FFFF",
    "#AFCCFF",
    "#F4C400",
    "#F52A2A",
    "#F63366"
    ]

#import the nodes.dmp
nodes_dict = {}
with open(nodes, "r") as infile:
    for line in infile:
        cols = line.split("\t|\t")
        taxid = cols[0]
        parent = cols[1]
        rank = cols[2]
        nodes_dict[taxid] = (parent, rank)
    else:
        nodes_dict["0"] = ("0", "unclassified")

read2taxid_dict = {}
with open(read2taxid, "r") as infile:
    for line in infile:
        cols = line.split("\t")
        read = cols[1]
        taxid = cols[2].strip("\n")
        while True:
            if taxid == "0" or taxid == "1":
                break
            if taxid in Rank_id:
                read2taxid_dict[read] = taxid
                break
            else:
                try:
                    taxid = nodes_dict[taxid][0]
                except:
                    taxid = "0"

read2taxonomy_dict = {}
with open(read2taxonomy, "r") as infile:
    for line in infile:
        cols = line.split("\t")
        read = cols[1]
        read2taxonomy_dict[read] = cols[2].strip("\n")

mapped_reads = 0
gene2read_dict = {}
with open(gene2read, "r") as infile:
    for line in infile:
        cols = line.split("\t")
        gene = cols[0]
        gene_len = cols[1]
        reads = []
        for read in cols[3:]:
            reads.append(read.strip("\n"))
        mapped_reads += len(reads)
        if gene in gene2read_dict:
            gene2read_dict[gene][1].extend(reads)
        else:
            gene2read_dict[gene] = (gene_len, reads)

EC2genes_dict = {}
with open(gene2EC, "r") as infile:
    for line in infile:
        cols = line.split("\t")
        gene = cols[0]
        EC = cols[1].strip("\n")
        if EC in EC2genes_dict:
            EC2genes_dict[EC].append(gene)
        else:
            EC2genes_dict[EC] = [gene]

RPKM_dict = {}
#gene2read_dict is a table with genes on one side, and the reads that make it up on the other (in a list)
#the table contains (gene ID, the length, the number of reads, the constituent read IDs themselves)
#Javi note: This piece of code is actually a little weird.
for gene in gene2read_dict:
    RPKM_div = ((float(gene2read_dict[gene][0])/float(1000))*(mapped_reads/float(1000000)))
    RPKM_dict[gene] = [gene2read_dict[gene][0], len(gene2read_dict[gene][1])]
    for EC in EC2genes_dict:
        if gene in EC2genes_dict[EC]:
            RPKM_dict[gene].append(EC)
            break
    else:
        RPKM_dict[gene].append("0.0.0.0")
    
    RPKM_dict[gene].append(len(gene2read_dict[gene][1])/RPKM_div)
    
    unclassified_reads = 0
    for taxa in Rank_id:
        read_count = 0
        for read in gene2read_dict[gene][1]:
            try:
                if read2taxid_dict[read] == taxa:
                    read_count += 1
            except:
                unclassified_reads += 1
        else:
            RPKM_dict[gene].append(read_count / RPKM_div)
    else:
        RPKM_dict[gene].append(unclassified_reads / RPKM_div)

RPKM_taxonomy_dict = {}
for gene in gene2read_dict:
    RPKM_div = ((float(gene2read_dict[gene][0])/float(1000))*(mapped_reads/float(1000000)))
    gene_EC_val = ""
    for EC in EC2genes_dict:
        if gene in EC2genes_dict[EC]:
            gene_EC_val = EC
            break
    else:
        gene_EC_val = "0.0.0.0"
    taxon2read_dict = {} 
    for read in gene2read_dict[gene][1]:
        taxon = read2taxonomy_dict[read]
        if taxon in taxon2read_dict:
            taxon2read_dict[taxon].append(read)
        else:
            taxon2read_dict[taxon] = []
            taxon2read_dict[taxon].append(read)
            #taxon2read_dict[taxon] = [read]
    for taxon in taxon2read_dict:
        RPKM_taxonomy_dict[gene+"||"+taxon] = [gene, taxon, gene2read_dict[gene][0], len(taxon2read_dict[taxon]), gene_EC_val]
        RPKM_taxonomy_dict[gene+"||"+taxon].append(len(taxon2read_dict[taxon])/RPKM_div)

with open(RPKM, "w") as RPKM_out:
    RPKM_out.write("GeneID\tTaxonomy\tLength\tReads\tEC#\tRPKM\n")
    for entry in RPKM_taxonomy_dict:
        RPKM_out.write("\t".join(str(x) for x in RPKM_taxonomy_dict[entry]) + "\n")


Cytoscape_dict = {}
for EC in EC2genes_dict:
    for entry in RPKM_dict:
        if RPKM_dict[entry][2] == EC:
            try:
                for index, RPKM_val in enumerate(Cytoscape_dict[EC]):
                    Cytoscape_dict[EC][index] += RPKM_dict[entry][3 + index]
            except:
                Cytoscape_dict[EC] = RPKM_dict[entry][3:]
    try:
        Cytoscape_dict[EC].append("piechart: attributelist=\"" + ",".join(str(x) for x in Rank) + "\" colorlist=\"" + ",".join(str(x) for x in Rank_colour) + ",#000000" + "\" showlabels=false\"")
    except:
        pass
with open(Cytoscape, "w") as Cytoscape_out:
    Cytoscape_out.write("EC#\tRPKM\t" + "\t".join(str(x) for x in Rank) + "\tOther\tPiechart\n")
    for entry in Cytoscape_dict:
        Cytoscape_out.write(entry + "\t" + "\t".join(str(x) for x in Cytoscape_dict[entry]) + "\n")