"""
Automically generate the pdf/eps/svg files from the tikz diagram

basic usage:
    >>> # to generate the pdf files from all the tikzpicture
    >>> tikz_export.py basic.tex -f pdf
    >>> # to generate the eps files from all the tikzpicture
    >>> tikz_export.py basic.tex -f eps
    >>> # to change the output filename, the output filename will be
    >>> # myfile0.eps myfile1.eps, ...
    >>> tikz_export.py basic.tex -f eps -o myfile
    >>> # only keep the 5th image
    >>> tikz_export.py basic.tex -f eps -n 5
    >>> # only keep the image with filename *my*
    >>> tikz_export.py basic.tex -f eps --fig *my*
Note: you can also define the filename for each tizkpicture by adding the
following line (start with '%%% ') before the tikzpicture. For example,

%%% mypicture
\begin{tikzpicture}
..
\end{tikzpicture}
Then the exported file will have name "mypicture.pdf/svg/eps"
"""

import sys, os, traceback, fnmatch, re
import glob
import click

tex2pdf_external = (
    '\\usetikzlibrary{external}\n'
    '\\tikzset{external/system call={pdflatex \\tikzexternalcheckshellescape'
    '-halt-on-error -interaction=batchmode -jobname "\\image" "\\texsource"'
    '}}\n'
    '\\tikzexternalize[shell escape=-enable-write18]\n\n')

pdf_export_cmd = {'.eps': "pdftops -eps", '.svg': "pdf2svg"}

@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--output-prefix', '-o', help="output file prefix")
@click.option('--dest', '-d', default='.', help="destination folder")
@click.option('--fmt', '-f', default='pdf',
              type=click.Choice(['pdf', 'svg', 'eps']),
              help="output file format")
@click.option('--number', '-n', multiple=True, help="output the nth figure")
@click.option('--fig', multiple=True, help="the name of figure to be output")
def cli(filename, output_prefix, dest, fmt, number, fig):
    inputfile = filename
    if not fmt.startswith('.'):
        fmt = '.'+fmt
    figs = number
    def is_enable(fidx, fname):
        """check whether need to output the figure"""
        enable = (not figs) or (fidx in figs)
        if enable:
            if not fig:
                return True
            for f in fig:
                if fnmatch.fnmatch(fname, f):
                    return True
        return False

    with open(inputfile) as fin:
        content = fin.readlines()
        ftemp = open('temp.tex', 'w')
        output_en = True
        fig_idx = 0
        fnames = []
        fname = ''
        for c in content:
            if re.search(r'\\begin(\s)*{(\s)*document(\s)*}', c):
                ftemp.write((tex2pdf_external))
                ftemp.write("%s"%c)
                output_en = False
            elif re.search(r'\\begin(\s)*{(\s)*tikzpicture', c):
                output_en = is_enable(fig_idx, fname)
                fig_idx += 1
                if output_en:
                    fnames.append(fname)
                fname = ''
            elif re.search(r'\\end(\s)*{(\s)*document}', c):
                ftemp.write("%s"%c)
                break
            elif re.search(r'\\end(\s)*{(\s)*tikzpicture(\s)*}', c):
                if output_en:
                    ftemp.write("%s"%c)
                output_en = False
            elif c.startswith("%%% "):
                fname = c[4:].strip()
            if output_en:
                ftemp.write("%s"%c)
        ftemp.close()

        # get the default output filename
        base = os.path.basename(inputfile)
        base = os.path.splitext(base)[0]
        if not output_prefix:
            output_prefix = base+'-figure'

        os.system(r"pdflatex --shell-escape temp.tex")
        for f in glob.glob('temp-figure*.pdf'):
            idx = int(f[11:-4])
            fout = ''
            if fnames[idx]:
                fn, fe = os.path.splitext(fnames[idx])
                if not fe:
                    fe = fmt
            else:
                fn, fe = "%s%d"%(output_prefix, idx), fmt
            fout = os.path.join(dest, fn+fe)
            click.echo("generating: %s"%fout)
            if fe != ".pdf":
                os.system(r"%s %s %s"%(pdf_export_cmd[fe], f, fout))
            else:
                os.system("del %s"%(fout))
                os.rename(f, fout)

        os.system("del temp*.*")

if __name__ == "__main__":
    cli()
