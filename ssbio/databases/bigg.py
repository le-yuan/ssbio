import json
import requests
import tempfile
import ssbio.databases.pdb
import ssbio.utils
import os.path as op
from bioservices.uniprot import UniProt
bs_unip = UniProt()


def get_pdbs_for_gene(bigg_model, bigg_gene, cache_dir=tempfile.gettempdir()):
    """Attempt to get a rank-ordered list of available PDB structures for a BiGG Model and its gene.

    Args:
        bigg_model: BiGG Model ID
        bigg_gene: BiGG Gene ID

    Returns:
        list: rank-ordered list of tuples of (pdb_id, chain_id)

    """
    my_structures = []

    outfile = op.join(cache_dir, '{}_genes.json'.format(bigg_model))
    if not op.exists(outfile):
        gene_raw = requests.get('http://bigg.ucsd.edu/api/v2/models/{}/genes/{}'.format(bigg_model, bigg_gene))
        gene = gene_raw.json()
        with open(outfile, 'w') as f:
            json.dump(gene, f)
    else:
        with open(outfile, 'r') as f:
            gene = json.load(f)

    uniprots = []
    if 'database_links' in gene:
        if 'UniProt' in gene['database_links']:
            uniprots = [x['id'] for x in gene['database_links']['UniProt']]
        elif 'NCBI GI' in gene['database_links']:
            uniprots = []
            gis = [x['id'] for x in gene['database_links']['NCBI GI']]
            gi_uniprots = bs_unip.mapping(fr='P_GI', to='ACC', query=gis).values()
            uniprots.extend(gi_uniprots)
            uniprots = ssbio.utils.flatlist_dropdup(uniprots)

    if uniprots:
        for u in uniprots:
            get_best_structure = ssbio.databases.pdb.best_structures(uniprot_id=u, outdir=cache_dir)
            if get_best_structure:
                for best_structure in get_best_structure:
                    my_structures.append((best_structure['pdb_id'], best_structure['chain_id']))

    return my_structures
