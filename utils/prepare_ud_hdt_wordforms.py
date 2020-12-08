"""
Extract word form transformation dictionaries from the UD German-HDT
"""
import argparse
import os
from glob import glob
from pprint import pprint

# todo: see about adding NOUN transform tags (to include person, number and syntactic case)
UPOS_TARGETS = ['VERB', 'AUX', 'DET']


def get_morph_tag(upos, udfeats):
    feats_list = udfeats.split('|')
    if upos == 'VERB' or upos == 'AUX':
        if 'VerbForm=Inf' in feats_list:
            return 'INF'
        elif 'VerbForm=Part' in feats_list:
            return 'PART'
        elif 'Number=Sing' in feats_list:
            if 'Person=1' in feats_list:
                return 'V1Sg'
            elif 'Person=2' in feats_list:
                return 'V2Sg'
            elif 'Person=3' in feats_list:
                return 'V3Sg'
        elif 'Number=Plur' in feats_list:
            if 'Person=1' in feats_list:
                return 'V1Pl'
            elif 'Person=2' in feats_list:
                return 'V2Pl'
            elif 'Person=3' in feats_list:
                return 'V3Pl'
    elif upos == 'DET':
        if 'Case=Nom' in feats_list:
            return 'Nom'
        elif 'Case=Acc' in feats_list:
            return 'Acc'
        elif 'Case=Dat' in feats_list:
            return 'Dat'
        elif 'Case=Gen' in feats_list:
            return 'Gen'
    else:
        return None


def extract_word_forms(filename):
    word_forms = {}
    with open(filename, encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            # Disregard sentence id and text fields
            if line.startswith('#') or line.isspace():
                continue

            # Read tab-separated fields
            idx, text, lemma, upos, xpos, udfeats, parent, deprel, _, _ = line.split("\t")
            text = text.lower()

            if upos in UPOS_TARGETS:
                # Generate tag based on upos and udfeats
                morph_tag = get_morph_tag(upos, udfeats)
                # Bail out if no tag is found
                if morph_tag is None:
                    continue

                if lemma in word_forms:
                    if text not in word_forms[lemma]:
                        word_forms[lemma][text] = morph_tag
                else:
                    word_forms[lemma] = {text: morph_tag}
    f.close()
    pprint(word_forms)
    return word_forms


def create_transform_map(word_forms):
    transforms = {}
    for i in word_forms:
        if i == 'unknown' or not i.isalpha():
            continue
        for j in word_forms[i]:
            for k in word_forms[i]:
                if j == k or '-' in j or '-' in k:
                    continue
                key = j + '_' + k
                if key not in transforms:
                    transforms[key] = word_forms[i][j] + '_' + word_forms[i][k]
                key = k + '_' + j
                if key not in transforms:
                    transforms[key] = word_forms[i][k] + '_' + word_forms[i][j]
    return transforms


def ud2wordforms(hdt_dir):
    """
    Process the treebanks in the German-HDT directory. Yield dictionary from word
    transforms to tags

    :param hdt_dir: Directory with UD German-HDT files
    :return: dict
    """
    # Check for valid input dir
    if not os.path.isdir(hdt_dir):
        raise UserWarning(f"{hdt_dir} is not a valid path!")

    # Do the extraction
    transform_map = {}
    filenames = sorted(glob(os.path.join(hdt_dir, '*.conllu')))
    for filename in filenames:
        word_forms = extract_word_forms(filename)
        transforms = create_transform_map(word_forms)
        transform_map.update(transforms)
    return transform_map


def main():
    transform_map = ud2wordforms(args.hdt_dataset_path)
    with open(args.output, mode='w', encoding='utf-8') as f:
        for key in sorted(transform_map):
            f.write(key + ':' + transform_map[key])
            f.write('\n')
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=(
        "Extract word form transformation dictionaries from the UD German-HDT"
    ))
    parser.add_argument('hdt_dataset_path',
                        help='Path to the UD German-HDT dataset')
    parser.add_argument('--output',
                        help='Path to the output folder')
    args = parser.parse_args()
    main()
