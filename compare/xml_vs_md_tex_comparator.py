#!/usr/bin/python3

# SPDX-FileCopyrightText: Robert Ryszard Paciorek <rrp@opcode.eu.org>
# SPDX-License-Identifier: MIT

# Created with Gemini AI, 2026

import sys
import os
import re
import difflib
try:
    from rapidfuzz import fuzz
except ImportError:
    print("Błąd: Biblioteka 'rapidfuzz' nie jest zainstalowana. Uruchom: pip install rapidfuzz")
    sys.exit(1)

RATIO_LIMIT = 60
RATIO_FULL_MATCH = 100.0
NUM_OF_MATCHED_LINES = 3

# Kody ucieczki ANSI dla kolorowania wyjścia w terminalu
COLOR_MATCH = '\033[90m'
COLOR_PARTIAL_MATCH = '\033[97m'
COLOR_CHANGED = '\033[91m'
COLOR_NOCHANGED = '\033[96m'
COLOR_NOMATCH = '\033[93m'
COLOR_RESET = '\033[0m'

def format_diff(source, target):
    """
    Tworzy wizualną reprezentację różnic między linią źródłową a docelową.
    Braki oznaczane są czerwonym '•', nadmiary i zmiany - czerwonym tekstem.
    """
    matcher = difflib.SequenceMatcher(None, source, target)
    result = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.append(f"{COLOR_NOCHANGED}{target[j1:j2]}{COLOR_RESET}")
        elif tag == 'insert':
            result.append(f"{COLOR_CHANGED}{target[j1:j2]}{COLOR_RESET}")
        elif tag == 'delete':
            missing_len = i2 - i1
            result.append(f"{COLOR_CHANGED}{'•' * missing_len}{COLOR_RESET}")
        elif tag == 'replace':
            len_s = i2 - i1
            len_t = j2 - j1
            padding = '•' * (len_s - len_t) if len_s > len_t else ''
            result.append(f"{COLOR_CHANGED}{target[j1:j2]}{padding}{COLOR_RESET}")
            
    return ''.join(result)

def read_and_process_xml(filepath):
    """
    Wczytuje XML, usuwa komentarze XML, rozwiązuje <insertSourceCode> 
    i usuwa tagi (za wyjątkiem <m> i <img>).
    """
    base_dir = os.path.dirname(os.path.abspath(filepath))
    processed_lines = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            xml_text = f.read()
    except Exception as e:
        print(f"Błąd podczas wczytywania XML {filepath}: {e}")
        return []

    # Usuwanie komentarzy XML z zachowaniem liczby linii (zastępowanie znakami nowej linii)
    xml_text = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), xml_text, flags=re.DOTALL)
    
    lines = xml_text.split('\n')
    for i, line_content in enumerate(lines):
        line_no = i + 1
        
        # Obsługa dołączanych plików źródłowych
        insert_match = re.search(r'<insertSourceCode\s+file="([^"]+)"\s*/>', line_content)
        if insert_match:
            included_filename = insert_match.group(1)
            included_filepath = os.path.join(base_dir, included_filename)
            try:
                with open(included_filepath, 'r', encoding='utf-8') as inc_f:
                    for inc_line in inc_f:
                        # Włączamy pliki bez usuwania jakichkolwiek tagów (surowy kod źródłowy)
                        clean_line = inc_line.lstrip()
                        if clean_line.strip():
                            processed_lines.append({'text': clean_line.rstrip('\n'), 'line_no': line_no})
            except Exception as e:
                print(f"Ostrzeżenie: Nie można wczytać pliku {included_filepath} w linii {line_no}: {e}")
            continue

        # Zwykłe przetwarzanie linii - odrzucanie tagów poza <m> i <img>
        clean_line = re.sub(r'<(?!/?(?:m|img)\b)/?[^>]+>', '', line_content)
        clean_line = clean_line.replace('&gt;', '>')
        clean_line = clean_line.replace('&lt;', '<')
        clean_line = clean_line.replace('&amp;', '&')
        clean_line = clean_line.lstrip()
        
        if clean_line.strip():
            processed_lines.append({'text': clean_line.rstrip('\n'), 'line_no': line_no})
            
    return processed_lines

def protect_markdown(text):
    tags_dict = {}
    tag_counter = 0

    def get_placeholder(content):
        nonlocal tag_counter
        # Używamy markerów bez znaków formatujących (brak _, *, ~), aby nie zostały usunięte
        p = f"@@PTAG{tag_counter}@@"
        tags_dict[p] = content
        tag_counter += 1
        return p

    text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img alt="\1" src="\2">', text)
    
    # Zabezpieczenie przed usunięciem reszty znaków formatujących
    text = re.sub(r'<m>.*?</m>', lambda m: get_placeholder(m.group(0)), text)
    text = re.sub(r'<img.*?>', lambda m: get_placeholder(m.group(0)), text)
    
    # Niestandardowy inline kod w markdown: `[lang]kod` -> kod
    text = re.sub(r'[^`]`\[[^\]]+\](.*?)`', lambda m: get_placeholder(m.group(1)), text)
    # Zwykły inline kod `kod` -> kod
    text = re.sub(r'`(.*?)`', lambda m: get_placeholder(m.group(1)), text)
    
    return text, tags_dict

def process_markdown(text):
    # Usuwanie komentarzy (HTML-owych używanych w MD)
    text = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), text, flags=re.DOTALL)
    lines = text.split('\n')
    processed_lines = []
    in_multiline_code = False
    
    for i, line in enumerate(lines):
        line_no = i + 1
        
        if in_multiline_code:
            # Sprawdzanie zamknięcia bloku kodu
            if re.match(r'^\s*```[a-zA-Z0-9_-]*\s*$', line):
                in_multiline_code = False
                # Pomiń linię z zamykającym ``` całkowicie
            else:
                clean = line.lstrip()
                if clean:
                    processed_lines.append({'text': clean.rstrip('\n'), 'line_no': line_no})
            continue
            
        # Otwarcie bloku wieloliniowego
        if re.match(r'^\s*```[a-zA-Z0-9_-]*\s*$', line):
            in_multiline_code = True
            # Pomiń linię z otwierającym ``` całkowicie
            continue
            
        # Pomiń linie będące wyłącznie ciągiem znaków -, = w Markdown (np. nagłówki, linie podziału)
        if re.match(r'^\s*[-=]+\s*$', line):
            continue
            
        line, tags = protect_markdown(line)
        
        # Czyszczenie formatowania
        line = re.sub(r'[*_]+', '', line)
        line = re.sub(r'~~', '', line)
        line = re.sub(r'^#+\s+', '', line)
        line = re.sub(r'^>\s+', '', line)
        
        # Przywracanie chronionych bloków
        for p, original in tags.items():
            line = line.replace(p, original)
        
        line = re.sub(r' [^\s]*⮒', '⮒', line)
        for clean in line.split('⮒'):
            clean = clean.lstrip()
            if clean:
                processed_lines.append({'text': clean.rstrip('\n'), 'line_no': line_no})
            
    return processed_lines

def protect_latex(text):
    tags_dict = {}
    tag_counter = 0

    def get_placeholder(content):
        nonlocal tag_counter
        p = f"@@PTAG{tag_counter}@@"
        tags_dict[p] = content
        tag_counter += 1
        return p

    # Najpierw chronimy i wyjmujemy surowy kod z bloków wewnątrzliniowych,
    # zanim spróbujemy interpretować potencjalne znaki matematyczne ($)
    text = re.sub(r'\\(?:cpp|shell|python|verb|Verb)\{([^}]*)\}', lambda m: get_placeholder(m.group(1)), text)
    text = re.sub(r'\\(?:cpp|shell|python|verb|Verb)([^a-zA-Z*])(.*?)\1', lambda m: get_placeholder(m.group(2)), text)

    # Dopiero teraz transformujemy wzory matematyczne i grafikę do tagów XML
    text = re.sub(r'\$\$(.*?)\$\$', r'<m>\1</m>', text)
    text = re.sub(r'\$(.*?)\$', r'<m>\1</m>', text)
    text = re.sub(r'\\includegraphics(?:\[(.*?)\])?\{(.*?)\}', r'<img alt="\1" src="\2">', text)
    
    # Chronimy wygenerowane tagi XML przed usunięciem w kolejnych krokach czyszczenia
    text = re.sub(r'<m>.*?</m>', lambda m: get_placeholder(m.group(0)), text)
    text = re.sub(r'<img.*?>', lambda m: get_placeholder(m.group(0)), text)
    
    return text, tags_dict

def process_latex(text):
    lines = text.split('\n')
    processed_lines = []
    in_multiline_code = False
    
    for i, line in enumerate(lines):
        line_no = i + 1
        
        if in_multiline_code:
            if re.search(r'\\end\{(CodeFrame|CodeFrame\*|Verbatim|minted)\}', line):
                in_multiline_code = False
                # Pomiń linię z \end całkowicie
                continue
            else:
                clean = line.lstrip()
                if clean:
                    processed_lines.append({'text': clean.rstrip('\n'), 'line_no': line_no})
            continue
            
        if re.search(r'\\begin\{(CodeFrame|CodeFrame\*|Verbatim|minted)\}', line):
            in_multiline_code = True
            # Pomiń linię z \begin całkowicie
            continue
            
        # Puste wartości dla innych środowisk
        line = re.sub(r'\\begin\{[^}]*\}(?:\[[^\]]*\])*(?:\{[^}]*\})*', '', line)
        line = re.sub(r'\\end\{[^}]*\}', '', line)
        
        # Chronienie tagów oraz wyciąganie surowego kodu z bloków wewnątrzliniowych przed usunięciem komentarzy %
        line, tags = protect_latex(line)
        
        # Usuwanie komentarzy niewyeskejpowanych (teraz bezpiecznie, bo inline code jest już schowany)
        line = re.sub(r'(?<!\\)%.*', '', line)
        
        # Czyszczenie formatowania LaTeX
        line = re.sub(r'\\vspace\{[^}]*\}', '', line)
        line = re.sub(r'\\[a-zA-Z]+\{([^{}]*)\}', r'\1', line)
        line = re.sub(r'\\[a-zA-Z]+\{([^{}]*)\}', r'\1', line)
        line = re.sub(r'\\[a-zA-Z]+', '', line)
        line = line.replace(r'\\', '')
        line = line.replace('~', ' ')
        
        # Przywracanie tagów
        for p, original in tags.items():
            line = line.replace(p, original)
            
        clean = line.lstrip()
        if clean:
            processed_lines.append({'text': clean.rstrip('\n'), 'line_no': line_no})
            
    return processed_lines

def process_bbcode(text):
    lines = text.split('\n')
    processed_lines = []
    for i, line in enumerate(lines):
        line_no = i + 1
        # Usunięcie tagów (cokolwiek w nawiasach), oprócz [lb]
        line = re.sub(r'\[(?!lb\]).*?\]', '', line)
        # Zamiana ocalałych [lb] na [
        line = line.replace('[lb]', '[')
        clean = line.lstrip()
        if clean:
            processed_lines.append({'text': clean.rstrip('\n'), 'line_no': line_no})
    return processed_lines

def process_txt(text):
    lines = text.split('\n')
    processed_lines = []
    for i, line in enumerate(lines):
        line_no = i + 1
        clean = line.lstrip()
        if clean:
            processed_lines.append({'text': clean.rstrip('\n'), 'line_no': line_no})
    return processed_lines

def route_and_process_file(filepath):
    """Przekierowuje wczytany plik do odpowiedniego parsera po rozszerzeniu."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Błąd podczas wczytywania pliku {filepath}: {e}")
        return []

    if ext == '.tex':
        return process_latex(text)
    elif ext == '.md':
        return process_markdown(text)
    elif ext in ['.not_edit', '.bbcode']:
        return process_bbcode(text)
    else:  # Domyślnie traktuj jako plik tekstowy (.txt i inne)
        return process_txt(text)

def compare_and_report(target_lines, xml_lines, filename):
    print(f"\n--- Plik: {filename} ---")
    all_best_ratios = []
    
    # Strumieniowe kalkulowanie wyników i jednoczesne wypisywanie do terminala
    for target_line in target_lines:
        scored_xml_lines = []
        for xml_line in xml_lines:
            similarity = fuzz.ratio(target_line['text'], xml_line['text'])
            if similarity >= RATIO_LIMIT:
                scored_xml_lines.append((similarity, xml_line))
            
        scored_xml_lines.sort(key=lambda x: x[0], reverse=True)
        if scored_xml_lines and re.match(r"^(#|//)", scored_xml_lines[0][1]['text']):
            xml_line2 = scored_xml_lines[0][1]['text']
            xml_line2 = re.sub(r"^(#|//) *", "", xml_line2)
            xml_line2 = re.sub(r"[`]+", "", xml_line2)
            similarity2 = fuzz.ratio(target_line['text'], xml_line2)
            if similarity2 > scored_xml_lines[0][0]:
                scored_xml_lines[0] = (similarity2, {'line_no': scored_xml_lines[0][1]['line_no'], 'text': xml_line2})
        
        best_ratio = scored_xml_lines[0][0] if scored_xml_lines else 0
        all_best_ratios.append(best_ratio)
        
        # Jeżeli znaleziona linia idealnie pasuje, to wypisujemy ją na szaro
        if best_ratio >= RATIO_FULL_MATCH:
            best_xml_line = scored_xml_lines[0][1]
            print(f"{COLOR_MATCH}{target_line['line_no']:>4}/{best_xml_line['line_no']:<4}: {target_line['text']}{COLOR_RESET}")
        else:
            # Wyszukanie w XML wszystkich linii, które przekroczyły próg RATIO_LIMIT
            valid_xml = [(r, x) for r, x in scored_xml_lines if r >= RATIO_LIMIT]
            
            if not valid_xml:
                # Brak pasujących linii >= RATIO_LIMIT w XML - wypisz źródłową na żółto
                print(f"{target_line['line_no']:>4}: {COLOR_NOMATCH}{target_line['text']}{COLOR_RESET}")
            else:
                # Wypisanie NUM_OF_MATCHED_LINES najbardziej podobnych linii (z tych co mają ratio >= RATIO_LIMIT)
                print(f"{target_line['line_no']:>4}:      {COLOR_PARTIAL_MATCH}{target_line['text']}{COLOR_RESET}")
                last_ratio = None
                for ratio, xml_line in valid_xml[:NUM_OF_MATCHED_LINES]:
                    if last_ratio and last_ratio-ratio > 10:
                        break
                    last_ratio = ratio
                    colored_diff = format_diff(target_line['text'], xml_line['text'])
                    print(f"  -> {xml_line['line_no']:>4}: {colored_diff} [{ratio:.2f}]")
                print("")
                    
    avg_ratio = sum(all_best_ratios) / len(all_best_ratios) if all_best_ratios else 0
    print(f"--- Koniec pliku: {filename} (średnie ratio: {avg_ratio:.2f}%) ---")

def main():
    if len(sys.argv) < 3:
        print("Użycie: python compare_docs.py <plik_xml> <plik_md_tex_txt_bbcode_1> [plik_2 ...]")
        sys.exit(1)
        
    xml_filepath = sys.argv[1]
    targets_filepaths = sys.argv[2:]
    
    print(f"Wczytywanie i przetwarzanie pliku XML: {xml_filepath} ...")
    xml_lines = read_and_process_xml(xml_filepath)
    
    if not xml_lines:
        print("Błąd: Plik XML jest pusty lub nie został poprawnie wczytany.")
        sys.exit(1)
        
    print(f"Wczytywanie i przetwarzanie pozostałych plików")
    
    for target_filepath in targets_filepaths:
        if not os.path.exists(target_filepath):
            print(f"\nPlik nie istnieje: {target_filepath}")
            continue
            
        target_lines = route_and_process_file(target_filepath)
        compare_and_report(target_lines, xml_lines, target_filepath)

if __name__ == "__main__":
    main()
