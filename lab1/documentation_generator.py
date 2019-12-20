import os
import shutil
from datetime import datetime

documentation_path = ""
project_name = ""

class Documentation:
    def __init__(self, path, relpath = "", prev_links = []):
        self.path = path
        self.name = os.path.basename(path)
        self.subdocumentations = []
        self.docs_and_names = []
        self.relpath = relpath

        #prev_links = prev_links
        #self.uplinks = prev_links

        # i hate python, it force me to do this :(
        self.uplinks = []
        for i in range(len(prev_links)):
            self.uplinks.append(prev_links[i])

        if self.relpath == "" :
            self.uplinks.append([project_name, project_name + ".html"])
        else:
            self.uplinks.append([self.name, self.relpath + ".html"])

        if os.path.isfile(self.path): # is file
            self.docs_and_names = []
            if (if_c_file(self.name)):
                self.docs_and_names = parse_into_documentation(self.path)     
        else: #is folder (or mb link)
            for subpath in os.listdir(self.path): # iterate all files/subfolders
                doc = Documentation(os.path.join(self.path, subpath), os.path.join(self.relpath, subpath), self.uplinks)
                self.subdocumentations.append(doc)

    def fill_names(self, names):
        names.append([self.relpath, self.relpath])
        if (len(self.docs_and_names) == 0):
            for i in range(len(self.subdocumentations)):
                self.subdocumentations[i].fill_names(names)
        else:
            isfile = os.path.isfile(self.path)
            for i in range(len(self.docs_and_names)):
                if (isfile):
                    subpath = os.path.join(documentation_path, self.path)
                    names.append([os.path.join(self.relpath, self.docs_and_names[i][1]), subpath])
                else:
                    names.append([self.docs_and_names[i][0], self.docs_and_names[i][1]]) # better use lib version

    def generate_content(self, path):
        body = ""
        if (len(self.docs_and_names) == 0):
            if (self.relpath != "" and os.path.isdir(self.path)):
                os.mkdir(path)
            
            for i in range(len(self.subdocumentations)):
                subpath = os.path.join(path, self.subdocumentations[i].name)
                body += wrap_with_tag(wrap_with_link_tag(self.subdocumentations[i].name, subpath + '.html'), "p")
                self.subdocumentations[i].generate_content(subpath) 
            
            body = add_navigation(body, self.uplinks)
            if (self.relpath == ""):
                generate_html(path, project_name, body)
            else:
                generate_html(os.path.dirname(path), self.name, body)
                
        else:
            # generate for specific file and add to body

            separator = wrap_with_tag("----------------------------------------------------", 'p')
            for i in range(len(self.docs_and_names)):
                body += wrap_with_tag('Name: ' + self.docs_and_names[i][1], 'p')
                body += wrap_with_tag('Doc: ' + wrap_with_tag(self.docs_and_names[i][0], 'pre'), 'p')
                body += separator

            body = add_navigation(body, self.uplinks)
            if (self.relpath == ""):
                generate_html(path, project_name, body)
                generate_html(path, self.name, body)
            else:
                generate_html(os.path.dirname(path), self.name, body) 
            pass
        
def if_c_file(name):
    if (len(name) >= 2 and name[-2:] == '.h'):
        return True
    elif (len(name) >= 2 and name[-2:] == '.c'):
        return True
    else:
        return False


def step(lines, i , j):
    inext = i
    jnext = j
    if (i == len(lines)):
        raise Exception("Troublesome code")
    jnext += 1
    if (jnext == len(lines[i])):
        jnext = 0
        inext += 1
    
    return inext, jnext

last_name = ""

def process_if_block(lines, i, j):
    global last_name
    name = ""
    if (lines[i][j] == '{'):
        istart = i
        jj = j
        while (jj >= 0):
            if (not lines[i][jj].isspace()):
                jstart = jj
            jj -= 1
        
        block_cnt = 1
        while (block_cnt > 0):
            i, j = step(lines, i, j)

            brk = False
            if (lines[i][j] == '#'):
                i = istart + 1
                j = jstart
                while (lines[i][j] != '}' and i < len(lines)):
                    i += 1

                #i, j = step(lines, i, j)
                #return True, i, j, ['N\A', name]
                brk = True

            if (brk):
                break;

            if (lines[i][j] == '{'):
                block_cnt += 1
            elif (lines[i][j] == '}'):
                block_cnt -= 1
        i, j = step(lines, i, j)
        
        if (lines[i][j] != ';' and (last_name.find("struct") != -1 or last_name.find("union") != -1 or last_name.find("enum") != -1)):
            if (last_name.find("struct") != -1 ):
                res = last_name.find("struct")
                name = 'struct '
            elif (last_name.find("union") != -1):
                res = last_name.find("union")
                name = 'union '
            elif (last_name.find("enum") != -1):
                res = last_name.find("enum")
                name = 'enum '
            else:
                raise Exception("Trouble with las_name")
            print("RES   ", res , "   ", res+len(name)-1 , "  ", len(last_name))
            
            truename = name[0:-1]
            sz = len(truename)
            if (res > 0 and not last_name[res-1].isspace()) or (
            res + sz + 1 < len(last_name) 
            and not (last_name[res+sz].isspace() or last_name[res+sz] == '\n')):
                pass
            else:
                while (i < len(lines) and lines[i][j] != ';'):
                    name += lines[i][j]
                    i, j = step(lines, i , j)
        
        if (lines[i][j] == ';'):
            i, j = step(lines, i, j)
        last_name = ""
        return True, i , j, ['N\\A', name]
    else:
        return False, i, j, ['N\\A', name]

def process_if_comment(lines, i , j):
    if (j < len(lines[i]) - 1 and lines[i][j] == '/' and lines[i][j + 1] == '/') :
        j = 0
        i += 1
        return True, i, j
    elif (j < len(lines[i]) - 1 and lines[i][j] == '/' and lines[i][j + 1] == '*') :
        i, j = step(lines, i, j)
        i, j = step(lines, i, j)
        found = False
        while not found:
            if (j < len(lines[i]) - 1 and lines[i][j] == '*' and lines[i][j + 1] == '/'):
                found = True
            else:
                i, j = step(lines, i, j)
        i, j = step(lines, i, j)
        i, j = step(lines, i, j)
        return True, i, j
    else:
        return False, i, j

def process_if_literal(lines, i, j):
    if (lines[i][j] == '"'):
        i, j = step(lines, i, j)
        while lines[i][j] != '"' :
            #print(i, ' ', j, ' ', lines[i][j])
            i, j = step(lines, i, j)
        i, j = step(lines, i, j)
        return True, i, j
    else:
        return False, i, j
  
def process_if_space(lines, i, j):
    found = False
    while (i < len(lines) and j < len(lines[i]) and (lines[i][j].isspace() or lines[i][j] == '\n')):
        found = True
        i, j = step(lines, i, j)
    return found, i, j


def doc_start(lines, i, j):
    oneline = False
    if (j < len(lines[i]) - 2 and lines[i][j] == '/' and lines[i][j + 1] == '*'):
        if (lines[i][j + 2] == '*' or lines[i][j + 2] == '!'):
            return True, oneline
        else:
            return False, oneline
    elif (j < len(lines[i]) - 2 and lines[i][j] == '/' and lines[i][j + 1] == '/'):
        if (lines[i][j + 2] == '*' or lines[i][j + 2] == '!' or lines[i][j + 2] == '/'):
            oneline = True
            return True, oneline
        else:
            return False, oneline
    else:
        return False, oneline

def doc_end(lines, i, j, oneline):
    if (oneline):
        if (lines[i][j] == '\n'):
            return True
        else:
            return False
    else:
        if (j < len(lines[i]) - 1 and lines[i][j] == '*' and lines[i][j + 1] == '/'):
            return True
        else:
            return False

def declaration_end(lines, i, j):
    if (lines[i][j] == '{' or lines[i][j] == ';'):
        return True
    else:
        return False

def process_if_doc(lines, i, j):
    doc = ""
    name = ""

    process = False
    is_oneline = False
    any_doc = False

    process, is_oneline = doc_start(lines, i, j)
    while (process):
        i, j = step(lines, i, j)
        i, j = step(lines, i, j)
        i, j = step(lines, i, j)
        
        any_doc = True
        while (not doc_end(lines, i, j, is_oneline)):
            doc += lines[i][j]
            i, j = step(lines, i, j)


        i, j = step(lines, i, j)
        if (not is_oneline):
            i, j = step(lines, i, j)
        
        dummy, i, j = process_if_space(lines, i, j)

        process, is_oneline = doc_start(lines, i, j)
        
    if (any_doc):
        if (lines[i][j] == '#'):
            name = lines[i][j:]
            j = 0
            i += 1
        else:
            while (not declaration_end(lines, i, j)):
                name += lines[i][j]
                i, j = step(lines, i, j)
            if (lines[i][j] == '{'):
                if (name[-2:] == '= ' or name[-2:] == '=\n'):
                    name = name[0:-2]
                elif (name[-1] == '='):
                    name[-1] = name[0:-1]

    return any_doc, i, j, [doc, name.strip()]

def procces_code(lines, i, j):
    name = ""

    if (lines[i][j] == ';'):
        i, j = step(lines, i, j)
        return i, j, []

    if (lines[i][j] == '#'):
        #name = lines [i][j :]
        i += 1
        j = 0
        #comment next line to count directives as names
        #name = ""
    else:
        while(not declaration_end(lines, i, j)):
            is_literal, inext, jnext = process_if_literal(lines, i, j)
            #print(i, ' ', j, '  ', inext, ' ', jnext)
            if (is_literal):
                while (i < inext or inext == i and j < jnext):
                    #print(i, ' ', j, ' ', name)
                    name += lines[i][j]
                    i, j = step(lines, i, j)
            else:
                name += lines [i][j]
                i, j = step(lines, i, j)
        if (lines[i][j] == '{'):
            if (name[-2:] == '= ' or name[-2:] == '=\n'):
                name = name[0:-2]
            elif (name[-1] == '='):
                name[-1] = name[0:-1]
    return i, j, ['N/A', name]

def parse_into_documentation(path):
    global last_name
    file = open(path, 'r')
    print(path)
    lines = file.readlines()
    file.close()
    res = []
    i = 0
    j = 0

    while (i != len(lines)):
        doc_and_name = []
        processed = False
        iold = i
        jold = j
        
        processed, i, j = process_if_space(lines, i, j)
        if (processed):
            print("from (", iold, ", ", jold, ") to (", i, ', ', j, ') space')
            continue

        processed, i, j, doc_and_name = process_if_doc(lines, i, j)
        if (processed):
            if (len(doc_and_name) > 0 and len(doc_and_name[1]) > 0  ):
                last_name = doc_and_name[1]
                res.append(doc_and_name)
            print("from (", iold, ", ", jold, ") to (", i, ', ', j, ') doc = ', doc_and_name)
            continue

        processed, i, j = process_if_comment(lines, i, j)
        if (processed):
            print("from (", iold, ", ", jold, ") to (", i, ', ', j, ') comment')
            continue

        processed, i, j = process_if_literal(lines, i, j)
        if (processed):
            print("from (", iold, ", ", jold, ") to (", i, ', ', j, ') literal')
            continue

        processed, i, j, doc_and_name = process_if_block(lines, i, j)
        if (processed):
            if (len(doc_and_name) > 0 and len(doc_and_name[1]) > 0 ):
                last_name = doc_and_name[1]
                res.append(doc_and_name)

            if (i < len(lines)):
                print("from (", iold, ", ", jold, ") to (", i, ', ', j, ') block last_name = ', last_name, ' $ cur_i = ', lines[i][0:-1])
            continue
        
        i, j, doc_and_name = procces_code(lines, i , j)
        if (i < len(lines)):
            print("from (", iold, ", ", jold, ") to (", i, ', ', j, ') code  cur_i = ', lines[i][0:-1])
        if (len(doc_and_name) > 0 and len(doc_and_name[1]) > 0 ):
            last_name = doc_and_name[1]
            res.append(doc_and_name)

    return res


def wrap_with_tag(body, tag):
    res = '<' + tag + '>' + body + '</' + tag + '>'
    return res

def wrap_with_link_tag(body, link):
    res = '<a href ="' + link + '\">' + body + '</a>'
    return res 

def head_tag_with_title(title):
    head = wrap_with_tag('<meta charset="UTF-8">' + wrap_with_tag(title, 'title'), 'head')
    return head

def html_tag(head, body):
    html = '<!DOCTYPE html>' + head + body + '</html>' 
    return html

def generate_html(folder, title, body):
    head = head_tag_with_title(title)
    body2 = wrap_with_tag(body, 'body')
    html = html_tag(head, body2)
    file = open(os.path.join(folder, title + '.html'), "w+")
    file.write(html)
    file.close()
    #save $title.html on folder

def add_navigation(body, lst):
    navigation = wrap_with_tag(wrap_with_link_tag("Header", os.path.join(documentation_path, "Header.html")) + '\t', 'span')
    navigation += wrap_with_tag(wrap_with_link_tag("Subject Index",os.path.join(documentation_path, "Subject_Index.html")) + '\t', 'span')
    
    if len(lst) == 0:
        navigation += wrap_with_tag(wrap_with_link_tag(project_name ,os.path.join(documentation_path, project_name + ".html")), 'span')
    else:
        for i in range(len(lst)):
            navigation += wrap_with_tag(wrap_with_link_tag(lst[i][0], os.path.join(documentation_path, lst[i][1])) + '/','span')
        
    navigation += wrap_with_tag("", 'p')
    navigation += wrap_with_tag("----------------------------------------------------", 'p')
    return navigation + body


def generate_header(doc_folder):
    global project_name
    name = "Project name: " + project_name
    version = 'Version: 0.0.1'
    date = "Generation time: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    generator_name = "Generator's name: C language documentation generator"
    body = wrap_with_tag(name, 'p') + wrap_with_tag(version, 'p')
    body += wrap_with_tag(date, 'p') + wrap_with_tag(generator_name, 'p')

    body = add_navigation(body, [])
    generate_html(doc_folder, 'Header', body)

def generate_subject_index(doc_folder, documentation):
    names = []
    documentation.fill_names(names)
    names.sort()

    body = ''
    for i in range(len(names)):
        body += wrap_with_tag(wrap_with_link_tag(names[i][0], names[i][1] + '.html'), 'p')

    body = add_navigation(body, [])
    generate_html(doc_folder, 'Subject_Index', body)

def generate_content(doc_folder, documentation):
    documentation.generate_content(doc_folder)

def generate_documentation(path, doc_folder, project_name_local):
    global project_name
    global documentation_path
    
    project_name = project_name_local
    
    doc_folder = os.path.abspath(doc_folder)
    if os.path.exists(doc_folder):
        shutil.rmtree(doc_folder, ignore_errors = True)
        #print("doc folder with such path exists, pls delete by hands and repeat generation")
        #exit()

    documentation = Documentation(path)

    os.mkdir(doc_folder)
    doc_folder = os.path.abspath(doc_folder)
    documentation_path = doc_folder

    generate_header(doc_folder)
    generate_subject_index(doc_folder, documentation)
    generate_content(doc_folder, documentation)

    print("Documentation successfully generated")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='C documentation generator')
    parser.add_argument("--path", help="Path to the folder with С files", required=True)
    parser.add_argument("--output", help="Path to the folder where html files will be generated", required=True)
    parser.add_argument("--project-name", help="Name of your project",required=True)
    args = parser.parse_args()
    generate_documentation(args.path, args.output, args.project_name)
    exit()
