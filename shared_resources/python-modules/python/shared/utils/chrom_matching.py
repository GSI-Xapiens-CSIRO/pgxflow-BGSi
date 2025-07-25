import subprocess


CHROMOSOME_ALIASES = {
    "M": "MT",
    "x": "X",
    "y": "Y",
}

CHROMOSOME_LENGTHS_MBP = {
    "1": 248.956422,
    "2": 242.193529,
    "3": 198.295559,
    "4": 190.214555,
    "5": 181.538259,
    "6": 170.805979,
    "7": 159.345973,
    "8": 145.138636,
    "9": 138.394717,
    "10": 133.797422,
    "11": 135.086622,
    "12": 133.275309,
    "13": 114.364328,
    "14": 107.043718,
    "15": 101.991189,
    "16": 90.338345,
    "17": 83.257441,
    "18": 80.373285,
    "19": 58.617616,
    "20": 64.444167,
    "21": 46.709983,
    "22": 50.818468,
    "X": 156.040895,
    "Y": 57.227415,
    "MT": 0.016569,
}

CHROMOSOMES = CHROMOSOME_LENGTHS_MBP.keys()


class ChromosomeNotFoundError(Exception):
    def __init__(self, chromosome_name):
        self.chromosome_name = chromosome_name
        super().__init__(f"No matching chromosome found for '{chromosome_name}'")


def get_vcf_chromosomes(vcf):
    args = ["tabix", "--list-chroms", vcf]
    tabix_output = subprocess.check_output(args=args, cwd="/tmp", encoding="utf-8")
    return tabix_output.split("\n")[:-1]


def get_matching_chromosome(vcf_chromosomes, target_chromosome):
    for vcf_chrom in vcf_chromosomes:
        if match_chromosome_name(vcf_chrom) == target_chromosome:
            return vcf_chrom
    return None


def get_regions(slice_size_mbp):
    regions = {}
    for chrom, size in CHROMOSOME_LENGTHS_MBP.items():
        chrom_regions = []
        start = 0
        while start < size:
            chrom_regions.append(start)
            start += slice_size_mbp
        regions[chrom] = chrom_regions
    return regions


def get_chromosome_mapping(vcf):
    vcf_chroms = get_vcf_chromosomes(vcf)
    return {chrom: match_chromosome_name(chrom) for chrom in vcf_chroms}


def match_chromosome_name(chromosome_name):
    for i in range(len(chromosome_name)):
        chrom = chromosome_name[i:]  # progressively remove prefix
        if chrom in CHROMOSOMES:
            return chrom
        elif chrom in CHROMOSOME_ALIASES:
            return CHROMOSOME_ALIASES[chrom]
    raise ChromosomeNotFoundError(chromosome_name)
