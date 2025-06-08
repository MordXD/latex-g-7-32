# LaTeX документы

Эта папка содержит LaTeX документы проекта ГОСТ 7-32.

## Структура

- `main.tex` - основной документ курсовой работы
- `aicalendar.tex` - дополнительный документ
- `sources.bib` - библиография
- `styles/` - стили и классы ГОСТ 7-32
- `images/` - изображения для документов
- `scripts/` - Python скрипты для генерации графиков

## Компиляция

Для компиляции основного документа выполните:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Или используйте latexmk для автоматической компиляции:

```bash
latexmk -pdf main.tex
```

## Требования

- TeX Live 2020+ или MiKTeX
- Пакеты: babel, fontenc, inputenc, graphicx, amsmath, siunitx, circuitikz

## Генерация графиков

Для генерации графиков запустите скрипты из папки `scripts/`:

```bash
cd scripts/
python generate_graphs.py
``` 