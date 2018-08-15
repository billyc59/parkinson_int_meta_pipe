import sys

raw_sequence = sys.argv[1]
quality_sequence = sys.argv[2]
rRNA_sequence = sys.argv[4]
mRNA_sequence = sys.argv[5]
gene_to_read_map = sys.argv[6]
ec_map = sys.argv[7]
output_file = sys.argv[8]

def fastq_count(fastq):
    lines = 0
    for item in fastq.split(","):
        with open(item, "r") as infile:
            for line in infile:
                lines += 1
            while lines % 4 != 0:
                lines -= 1

    return lines / 4

def annotated_count(map):
    annotated_mRNA = 0
    genes = 0
    with open(map, "r") as infile:
        for line in infile:
            genes += 1
            annotated_mRNA += int(line.split("\t")[2])

    return annotated_mRNA, genes

def ec_count(map):
    ecs = set()
    with open(map, "r") as infile:
        for line in infile:
            ecs.add(line.split("\t")[1].strip())

    return len(ecs)

headings = []
data = []

headings.append("Total reads")
raw_sequence_count = fastq_count(raw_sequence)
data.append(str(raw_sequence_count))

headings.append("High quality reads")
quality_sequence_count = fastq_count(quality_sequence)
data.append(str(quality_sequence_count))

headings.append("% high quality")
quality_sequence_pct = quality_sequence_count / raw_sequence_count
data.append("%.2f" % quality_sequence_pct)

headings.append("rRNA reads")
rRNA_sequence_count = fastq_count(rRNA_sequence)
data.append(str(rRNA_sequence_count))

headings.append("% rRNA reads")
rRNA_sequence_pct = rRNA_sequence_count / raw_sequence_count
data.append("%.2f" % rRNA_sequence_pct)

headings.append("Putative mRNA reads")
mRNA_sequence_count = fastq_count(mRNA_sequence)
data.append(str(mRNA_sequence_count))

headings.append("% putative mRNA reads")
mRNA_sequence_pct = mRNA_sequence_count / raw_sequence_count
data.append("%.2f" % mRNA_sequence_pct)

headings.append("Annotated mRNA reads")
annotated_mRNA_count, genes_count = annotated_count(gene_to_read_map)
data.append(str(annotated_mRNA_count))

headings.append("% of putative mRNA reads annotated")
annotated_mRNA_pct = annotated_mRNA_count / mRNA_sequence_count
data.append("%.2f" % annotated_mRNA_pct)

headings.append("Unique transcripts")
data.append(str(genes_count))

headings.append("Unique enzymes")
unique_ec_count = ec_count(ec_map)
data.append(str(unique_ec_count))

with open(output_file, "w") as outfile:
    outfile.write("\t".join(headings))
    outfile.write("\t".join(data))
