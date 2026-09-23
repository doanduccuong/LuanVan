$pdf_mode = 1;
$bibtex_use = 2;
$max_repeat = 5;
@default_files = ('LuanVan.tex');
$out_dir = '../output/pdf';

# Cho BibTeX tìm thấy file .bib khi toàn bộ file build nằm ở output/pdf.
use Cwd qw(getcwd);
$ENV{'BIBINPUTS'} = getcwd() . ':' . ($ENV{'BIBINPUTS'} // '');
