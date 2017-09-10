#!/usr/bin/env python
"""Test that two different but equivalent fishers functions give the similar results."""

import sys
import os
from itertools import combinations
import collections as cx
import xlrd

from goatools.go_enrichment import GOEnrichmentStudy
from goatools.base import get_godag
from goatools.test_data.genes_NCBI_10090_ProteinCoding import GeneID2nt as GeneID2nt_mus
from goatools.associations import get_assoc_ncbi_taxids

def test_pvalcalc(prt=None):
    """Test P-value calculations."""
    pvalfnc_names = ['fisher', 'fisher_scipy_stats']
    fisher2pvals = _get_pvals(pvalfnc_names)
    _chk_pvals(fisher2pvals, prt)

def _chk_pvals(fisher2pvals, prt):
    for fish1, fish2 in combinations(fisher2pvals.keys(), 2):
        ctr = cx.Counter()
        pvals1 = cx.OrderedDict(sorted([(r.GO, r.p_uncorrected) for r in fisher2pvals[fish1]]))
        pvals2 = cx.OrderedDict(sorted([(r.GO, r.p_uncorrected) for r in fisher2pvals[fish2]]))
        assert len(pvals1) == len(pvals2)
        for go_id, pval1 in pvals1.items():
            pval2 = pvals2[go_id]
            ctr[pval1 == pval2] += 1
            if prt is not None:
                # Are values from 'fisher' and scipy stats 'fisher_exact' equivalent?
                if abs(pval1 - pval2) > 0.00001:
                    prt.write("{GO} {N1}({P1:4.2f}) {N2}({P2:4.2f}) {N1}({p1}) {N2}({p2})\n".format(
                        GO=go_id, N1=fish1, N2=fish2, P1=pval1, P2=pval2, p1=pval1, p2=pval2))
        if prt is not None:
            pat = "{N:>5,} {RES:5}: {N1} == {N2}\n"
            for val, cnt in ctr.most_common():
                prt.write(pat.format(N=cnt, RES=val, N1=fish1, N2=fish2))

def _get_pvals(pvalfnc_names, prt=sys.stdout):
    fisher2pvals = {}
    taxid = 10090 # Mouse study
    file_obo = os.path.join(os.getcwd(), "go-basic.obo")
    obo_dag = get_godag(file_obo, prt, loading_bar=None)
    geneids_pop = GeneID2nt_mus.keys()
    assoc_geneid2gos = get_assoc_ncbi_taxids([taxid], loading_bar=None)
    geneids_study = _get_geneid2symbol("nbt.3102-S4_GeneIDs.xlsx")
    for fisher in pvalfnc_names:
        goeaobj = GOEnrichmentStudy(
            geneids_pop,
            assoc_geneid2gos,
            obo_dag,
            propagate_counts=False,
            alpha=0.05,
            methods=None,
            pvalcalc=fisher)
        fisher2pvals[fisher] = goeaobj.get_pval_uncorr(geneids_study, prt)
    return fisher2pvals

def _get_geneid2symbol(fin_xlsx):
    """Read xlsx file return dictionary with Entrez GeneID keys to Symbol data."""
    gene2symbol = {}
    data_dir = os.path.dirname(os.path.abspath(__file__)) + "/data/nbt_3102"
    tbl_genes = "{DIR}/{FIN}".format(DIR=data_dir, FIN=fin_xlsx)
    book = xlrd.open_workbook(tbl_genes)
    sheet = book.sheet_by_index(0)
    for row in range(sheet.nrows):
        symbol, geneid, _ = [sheet.cell_value(row, c) for c in range(sheet.ncols)] # pval
        if geneid:
            gene2symbol[int(geneid)] = symbol
    return gene2symbol

if __name__ == '__main__':
    test_pvalcalc(sys.stdout)
