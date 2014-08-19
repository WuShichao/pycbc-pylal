#!/usr/bin/env python
# read in all the first stage triggers, make a cut on new_snr, create the summary files,
# and calculate the livetime.
from glue.ligolw import ligolw
from glue.ligolw import lsctables
from glue.ligolw import utils
from glue.ligolw.utils import process
from glue import segmentsUtils
from glue import segments, git_version
from glue.lal import LIGOTimeGPS
import glob
import optparse
import sys

def get_loud_trigs(fList, veto_file, new_snr_cut):
    """ Return a list(s) of single inspiral triggers that are above the
        new snr threshold for every combination of file in the file list
        and application of veto in the veto file list.
    """
    trigs = lsctables.New(lsctables.SnglInspiralTable)
    searched_segs = segments.segmentlist()
    for fname in fList:
        xmldoc = utils.load_filename(fname, gz=True)
        tbl = lsctables.table.get_table(xmldoc, lsctables.SnglInspiralTable.tableName)
        trigs.extend([tbl[i] for i in (tbl.get_new_snr() > new_snr_cut).nonzero()[0]])
        search_summary = lsctables.table.get_table(xmldoc, lsctables.SearchSummaryTable.tableName)
        searched_segs += search_summary.get_outlist()

    if isinstance(veto_file, list):
        # If we have multiple veto files, return results for applying each one
        lt = []
        tg = []
        for vf in veto_file:
            veto_segs = segmentsUtils.fromsegwizard(open(vf))
            trig_sub = trigs.veto(veto_segs)
            searched_segs -= veto_segs
            livetime = abs(searched_segs)

            lt.append(livetime)
            tg.append(trig_sub)
        return tg, lt
    else:
        veto_segs = segmentsUtils.fromsegwizard(open(veto_file))
        trigs = trigs.veto(veto_segs)
        searched_segs -= veto_segs
        livetime = abs(searched_segs)
        return trigs, livetime

if __name__ == "__main__":
    parser = optparse.OptionParser()

    parser.add_option("-I","--input-glob",action="store",type="string",\
        default=None,metavar=" INPUT_GLOB",\
        help="GLOB of input inspiral xml files")

    parser.add_option("-c","--new-snr-cut",action="store",type="float",\
        default="6.0", help="new snr threshold to retain triggers")

    parser.add_option("--output-file",action="store",type="string",\
        default=None, help="Name of output file")

    parser.add_option("--veto-file",action="store",type="string",\
        default=None, help="Name of veto file")

    (opts,args) = parser.parse_args()

    if opts.input_glob:
      fList = glob.glob(opts.input_glob)
    else:
      print >>sys.stderr, "Must specify a GLOB of input files "
      sys.exit(1)

    if not opts.output_file:
      print >>sys.stderr, "Must specify an output file"
      sys.exit(1)

    if not opts.veto_file:
      print >>sys.stderr, "Must specify a veto file"
      sys.exit(1)

    trigs, livetime = get_loud_trigs(fList, opts.veto_file, opts.new_snr_cut)

    output_doc=ligolw.Document()
    output_doc.appendChild(ligolw.LIGO_LW())

    proc_id = process.register_to_xmldoc(output_doc,
                "get_loud_trigs", opts.__dict__, comment="", ifos=[""],
                version=git_version.id, cvs_repository=git_version.branch,
                cvs_entry_time=git_version.date).process_id

    vartable = lsctables.New(lsctables.SearchSummVarsTable)
    var = lsctables.SearchSummVars()
    var.process_id = proc_id
    var.value = livetime
    var.name = "livetime"
    var.string = "Single detector trigger collection time in seconds."
    var.search_summvar_id = vartable.next_id
    vartable.append(var)

    output_doc.childNodes[0].appendChild(vartable)
    output_doc.childNodes[0].appendChild(trigs)

    utils.write_filename(output_doc, opts.output_file, gz=opts.output_file.endswith("gz"))
