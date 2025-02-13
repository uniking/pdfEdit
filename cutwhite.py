import argparse
import logging
import os

from PyPDF2 import PdfWriter, PdfReader

import miner
from utils import get_logger

logger = get_logger(__name__, level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("-i", help="input file", action="store",
                    default='', type=str, dest="input")
parser.add_argument("-o", help="output file", action="store",
                    default='', type=str, dest="output")
parser.add_argument("-id", help="input directory", action="store",
                    default='', type=str, dest="indir")
parser.add_argument("-od", help="output directory", action="store",
                    default='', type=str, dest="outdir")
parser.add_argument("-t", "--test", help="run test",
                    action="store_true", dest="test")
parser.add_argument("--ignore", help="ignore global",
                    action="store", type=int, default=0, dest="ignore")
parser.add_argument("--verbose", help="choose verbose (DEBUG)",
                    action="store_true", default=False, dest="verbose")
# parser.add_argument(nargs=argparse.REMAINDER, dest="value")
args = parser.parse_args()


def fix_box(page, fix):
    """
    cut the box by setting new position (relative position)
    """
    box = page.mediabox
    logger.info('media box: %s', page.mediabox)
    logger.debug(page.trimbox)
    logger.debug(page.artbox)
    logger.debug(page.cropbox)
    logger.debug(page.bleedbox)

    # must translate relative position to absolute position
    # box position
    bx, by = box.lower_left
    bx = float(bx)
    by = float(by)
    bx2, by2 = box.upper_right
    bx2, by2 = float(bx2), float(by2)

    # given position to fix
    (x1, y1, x2, y2) = fix
    extraErae = 30
    # FIXME: 此处设置裁剪区域，可增加数值来修改裁剪的范围 LSX
    # FIXME: fixed position, choose the smaller area
    fx1, fy1, fx2, fy2 = max(bx, x1 + bx) +extraErae , max(by, y1 +
                                               by) +extraErae, min(bx2, x2 + bx)-extraErae, min(by2, y2 + by)-extraErae

    logger.info("origin box: %s", (box))

    box.lower_left = (fx1, fy1)
    box.upper_right = (fx2, fy2)

    logger.info("fixed box: %s", (box))


def cut_white(inpath, outpath: str = None, ignore=0):
    """
    cut the white slide of the input pdf file, and output a new pdf file.
    """
    if outpath is None:
        outpath = 'output.pdf'

    if inpath == outpath:
        raise Exception('input and output can not be the same!')

    try:
        pages = []
        with open(inpath, 'rb') as infd:
            logger.info('process file: %s', inpath)
            outpdf = PdfWriter()
            inpdf = PdfReader(infd)

            # get the visible area of the page, aka the box scale. res=[(x1,y1,x2,y2)]
            pageboxlist = miner.mine_area(inpath, ignore=ignore)

            num = len(inpdf.pages)
            for i in range(num):
                # scale is the max box of the page
                scale = pageboxlist[i]
                page = inpdf.pages[i]

                logger.info('origin scale: %s', scale)

                fix_box(page, scale)
                outpdf.add_page(page)

            if outpath:
                with open(outpath, 'wb') as outfd:
                    outpdf.write(outfd)
                    logger.info('output file: %s', outpath)

    except UnicodeEncodeError as ue:
        logger.exception('UnicodeEncodeError while processing file:%s', (inpath))
        logger.exception(ue)
    except Exception as e:
        logger.exception('Some other Error while processing file:%s', (inpath))
        logger.exception(e)


def scan_files(folder, prefix=None, postfix=None, sub=False):
    """
    scan files under the dir with spec prefix and postfix
    """
    files = []

    for item in os.listdir(folder):
        path = os.path.join(folder, item)
        if os.path.isfile(path):
            if postfix:
                if item.endswith(postfix):
                    files.append(item)

    return files


def batch(indir, outdir, ignore=0):
    if indir == outdir:
        raise Exception('input and output can not be the same!')

    files = scan_files(indir, postfix='pdf')
    logger.info(files)

    if not os.path.exists(indir):
        os.mkdir(indir)

    for item in files:
        inpath = os.path.join(indir, item)
        outpath = os.path.join(outdir, item)
        cut_white(inpath, outpath, ignore=ignore)


def test_one():
    inputfile = './input/input.pdf'
    outputfile = './output/output.pdf'
    cut_white(inputfile, outputfile)


def test_batch():
    outdir = './output'
    indir = './input'
    batch(indir, outdir)


def tests():
    test_one()
    test_batch()


if __name__ == "__main__":
    if args.verbose:
        logger.setLevel('DEBUG')

    if args.input and args.output:
        cut_white(args.input, args.output, args.ignore)
    elif args.input:
        cut_white(args.input, None, args.ignore)
    elif args.indir and args.outdir:
        batch(args.indir, args.outdir, args.ignore)
    elif args.test:
        tests()
    else:
        parser.print_help()
