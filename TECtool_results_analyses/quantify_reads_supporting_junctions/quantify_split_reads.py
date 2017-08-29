# _____________________________________________________________________________
# -----------------------------------------------------------------------------
# import needed (external) modules
# -----------------------------------------------------------------------------

try:
    import os
except(Exception):
    raise("[ERROR] os was not imported properly. Exiting.")
    sys.exit(-1)

try:
    from argparse import ArgumentParser, RawTextHelpFormatter, FileType
except(Exception):
    raise("[ERROR] argparse was not imported properly. Exiting.")
    sys.exit(-1)

try:
    import sys
except(Exception):
    raise("[ERROR] sys was not imported properly. Exiting.")
    sys.exit(-1)

try:
    import HTSeq
except(Exception):
    raise("[ERROR] HTSeq was not imported properly. Exiting.")
    sys.exit(-1)

try:
    import HTSeq
except(Exception):
    raise("[ERROR] HTSeq was not imported properly. Exiting.")
    sys.exit(-1)

# _____________________________________________________________________________
# -----------------------------------------------------------------------------
# Main function
# -----------------------------------------------------------------------------
def main():

    """ Main function """

    __doc__ = "Keep annotated terminal exons from gtf file"

    parser = ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)

    parser.add_argument("--tectool_installation_dir",
                        dest="tectool_installation_dir",
                        required=True,
                        help="The pathway to the directory to which TECtool was installed.")

    parser.add_argument("--bed_annotated",
                        dest="bed_annotated",
                        help="Bed file containing genomic coordinates of annotated terminal exons",
                        required=True,
                        metavar="FILE")

    parser.add_argument("--bed_novel",
                    dest="bed_novel",
                    help="Bed file containing genomic coordinates of novel terminal exons",
                    required=True,
                    metavar="FILE")

    parser.add_argument("--bam",
                        dest="bam",
                        help="Alignment file",
                        required=True,
                        metavar="FILE")

    parser.add_argument("--sequencing_direction", 
                        dest="sequencing_direction",
                        help="Sequencing direction: Options unstranded  or forward.",
                        required=True,
                        default="unstranded")

    parser.add_argument("--out",
                        dest="out",
                        help="Output directory",
                        required=True)

    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        dest="verbose",
                        default=False,
                        required=False,
                        help="Verbose")

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # get the arguments
    # -------------------------------------------------------------------------
    try:
        options = parser.parse_args()
    except(Exception):
        parser.print_help()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # _____________________________________________________________________________
    # -----------------------------------------------------------------------------
    # import our own modules
    # -----------------------------------------------------------------------------
    # import tectool classes
    sys.path.insert(0, options.tectool_installation_dir)

    from gene_structure import Exon
    from gene_structure import Transcript
    from gene_structure import Gene
    from aln_analysis import DetailedAlignment
    from aln_analysis import SplitEvent
    from aln_analysis import AnalysisUnit
    from aln_analysis import FeatureCounts
    from annotation import Annotation

    if options.verbose:
        sys.stdout.write("Script started...\n")

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Create output directories
    # -------------------------------------------------------------------------
    if not os.path.exists(options.out):
        os.makedirs(options.out)

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Open the BAM file
    # -------------------------------------------------------------------------
    bam = HTSeq.BAM_Reader(options.bam)

    # _________________________________________________________________________
    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # PART 1: NOVEL EXONS
    # -------------------------------------------------------------------------
    # _________________________________________________________________________
    # _________________________________________________________________________

    if options.verbose:
        sys.stdout.write("Working on novel terminal exons...\n")

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Open the bed file of novel exons
    # -------------------------------------------------------------------------
    bed_novel = HTSeq.BED_Reader(options.bed_novel)

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # CREATE an AnalysisUnit for each terminal exon
    # -------------------------------------------------------------------------
    aunits_novel = []

    for bed_entry in bed_novel:

        region_string = bed_entry.iv.chrom + ":" + str(bed_entry.iv.start) + "-" + str(bed_entry.iv.end)

        # initialize constructor for analysis unit
        au = AnalysisUnit(unit_id=region_string,
                          potential_5pSS_exons=None,
                          gene_id=bed_entry.name)

        # init gaos and iv
        au.gaos = HTSeq.GenomicArrayOfSets("auto", stranded=True)
        au.gaos[bed_entry.iv] += "exon"

        au.iv = bed_entry.iv

        aunits_novel.append(au)

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Go over the analysis units of novel exons and count/process the mappings
    # -------------------------------------------------------------------------
    unit_nr = 0
    for au in aunits_novel:
        unit_nr+=1

        # give some feedback about the state of the script
        # (how many units have been analyzed so far?)
        if (unit_nr % 100) == 0:
            sys.stdout.write("Regions processed:\t" + str(unit_nr) + "\n")
    
        # go over each alignment
        for aln in bam.fetch(region = au.unit_id):

            # In case we have unstranded data we change the 
            # strand for the ALIGNMENT and the CIGAR STRING
            if "unstranded" in options.sequencing_direction:
                
                if au.iv.strand is not aln.iv.strand:
                    aln.iv.strand = au.iv.strand
                    for co in aln.cigar:
                        co.ref_iv.strand = au.iv.strand

            au.count(aln,
                     sequencing_direction=options.sequencing_direction,
                     min_region_overlap=0,
                     splice_fuzziness=0,
                     count_unique_mapping_reads_only=True,
                     annotated = True,
                     verbose=False)        

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Count how many split reads we have for each novel terminal exons
    # -------------------------------------------------------------------------
    w = open(os.path.join(options.out, "counts_novel.tsv"), 'w')
    for au in aunits_novel:
        w.write("\t".join([":".join([au.iv.chrom, str(au.iv.start+1), str(au.iv.end), au.gene_id, au.iv.strand, "novel"]), str(au.annotated_splice_in_borders)+"\n"]))
    w.close()

    # _________________________________________________________________________
    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # PART 2: ANNOTATED EXONS
    # -------------------------------------------------------------------------
    # _________________________________________________________________________
    # _________________________________________________________________________

    if options.verbose:
        sys.stdout.write("Working on annotated terminal exons...\n")

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Open the bed file of annotated exons
    # -------------------------------------------------------------------------
    bed_annotated = HTSeq.BED_Reader(options.bed_annotated)

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # CREATE an AnalysisUnit for each annotates exon
    # -------------------------------------------------------------------------
    aunits_annotated = []

    for bed_entry in bed_annotated:

        region_string = bed_entry.iv.chrom + ":" + str(bed_entry.iv.start) + "-" + str(bed_entry.iv.end)

        # initialize constructor for analysis unit
        au = AnalysisUnit(unit_id=region_string,
                          potential_5pSS_exons=None,
                          gene_id=bed_entry.name)

        # init gaos and iv
        au.gaos = HTSeq.GenomicArrayOfSets("auto", stranded=True)
        au.gaos[bed_entry.iv] += "exon"

        au.iv = bed_entry.iv

        aunits_annotated.append(au)

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Go over the analysis units of annotated exons and count/process the 
    # mappings
    # -------------------------------------------------------------------------
    unit_nr = 0
    for au in aunits_annotated:
        unit_nr+=1

        # give some feedback about the state of the script
        # (how many units have been analyzed so far?)
        if (unit_nr % 100) == 0:
            sys.stdout.write("Regions processed:\t" + str(unit_nr) + "\n")
    
        # go over each alignment
        for aln in bam.fetch(region = au.unit_id):

            # In case we have unstranded data we change the 
            # strand for the ALIGNMENT and the CIGAR STRING
            if "unstranded" in options.sequencing_direction:
                
                if au.iv.strand is not aln.iv.strand:
                    aln.iv.strand = au.iv.strand
                    for co in aln.cigar:
                        co.ref_iv.strand = au.iv.strand

            au.count(aln,
                     sequencing_direction=options.sequencing_direction,
                     min_region_overlap=0,
                     splice_fuzziness=0,
                     count_unique_mapping_reads_only=True,
                     annotated = True,
                     verbose=False)

    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # Count how many split reads we have for each annotated terminal exons
    # -------------------------------------------------------------------------
    w = open(os.path.join(options.out, "counts_annotated.tsv"), 'w')
    for au in aunits_annotated:
        w.write("\t".join([":".join([au.iv.chrom, str(au.iv.start+1), str(au.iv.end), au.gene_id, au.iv.strand, "annotated"]), str(au.annotated_splice_in_borders)+"\n"]))
    w.close()

    # _________________________________________________________________________
    # _________________________________________________________________________
    # -------------------------------------------------------------------------
    # PART 3: FINALIZE OUTPUT FILE
    # -------------------------------------------------------------------------
    # _________________________________________________________________________
    # _________________________________________________________________________

    if options.verbose:
        sys.stdout.write("Concatenating annotated and novel terminal exons...")

    os.system("cat %s %s > %s" % (os.path.join(options.out, "counts_annotated.tsv"),
                                  os.path.join(options.out, "counts_novel.tsv"),
                                  os.path.join(options.out, "counts_annotated_and_novel.tsv")))

    if options.verbose:
        sys.stdout.write("Script done...\n")



# -----------------------------------------------------------------------------
# Call the Main function and catch Keyboard interrups
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("User interrupt!\n")
        sys.exit(0)
