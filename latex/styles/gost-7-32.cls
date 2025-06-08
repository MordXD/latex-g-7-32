\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{gost-7-32}[2024/03/10 GOST 7.32-2017 v1.1]

%
% Supported font sizes: 12pt, 14pt
%
\DeclareOption{12pt}{\PassOptionsToClass{\CurrentOption}{extarticle}}
\DeclareOption{14pt}{\PassOptionsToClass{\CurrentOption}{extarticle}}

\ProcessOptions\relax

%
% Set A4 paper format
%
\LoadClass[a4paper]{extarticle}

%
% Базовые настройки перенесены в соответствующие стили:
% - gost-7-32-paragraph-style.sty: для настройки абзацев и интервалов
% - gost-7-32-pagination.sty: для настройки нумерации страниц
%

%
% Page margin
%
\RequirePackage[
    left=3cm,
    right=1.5cm,
    top=2cm,
    bottom=2cm
]{geometry}

%
% Use TMR-like font
%
\RequirePackage{tempora}

%
% Use russian language
%
\RequirePackage[T2A]{fontenc}
\RequirePackage[utf8]{inputenc} % Warning: inputenc package ignored with utf8 based engines.
\RequirePackage[english, russian]{babel}
\AtBeginDocument{\fontencoding{T2A}\selectfont}

%
% gost-7-32 packages
%
\RequirePackage{gost-7-32-headings}
\RequirePackage{gost-7-32-toc}
\RequirePackage{gost-7-32-lists}
\RequirePackage{gost-7-32-bibliography}
\RequirePackage{gost-7-32-captions}
\RequirePackage{gost-7-32-tables}
\RequirePackage{gost-7-32-commands}
\RequirePackage{gost-7-32-title-page}
\RequirePackage{gost-7-32-code-style}
\RequirePackage{gost-7-32-graphics-style}
\RequirePackage{gost-7-32-table-style}
\RequirePackage{gost-7-32-paragraph-style}
\RequirePackage{gost-7-32-pagination}
\RequirePackage{gost-7-32-sections}

% Добавление поддержки кириллической буквы \CYRV в кодировке T1
% \DeclareTextSymbol{\CYRV}{T1}{{\fontencoding{T2A}\selectfont В}}
