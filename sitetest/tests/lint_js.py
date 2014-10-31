import gzip
import jsbeautifier
import os
import pyjslint
import urllib2
from itertools import izip

def test_lint_js(links, canonical_domain, domain_aliases, messages, verbose=False):
    """
    For each page, make sure there is a unique title and description
    """


    total_js_error_count = 0
    
    for link_url in links:
        link = links[link_url]
        link_type = link['type']
        content_type = link['response_content_type']

        if content_type and 'javascript' in content_type.lower():
            
            local_file_path = store_file_locally(link_url)
            #local_file_path = 'test.js'

            
            
            try:
                #Attempt to read as gzipped file
                f = gzip.open(local_file_path, 'rb')
                link_source = f.read()
                f.close()
            except:
                try:
                    #Attempt to read as uncompressed file
                    f = open(local_file_path, 'rb')
                    link_source = f.read()
                    f.close()

                    link['messages']['warning'].append("Warning: javascript file is not gzipped")

                except:
                    link_source = None

                    link['messages']['error'].append("Unable to read file")




            if link_source:

                beautified_link_source = jsbeautifier.beautify(link_source)

                #pyjslint.check_JSLint(file.read())                        
                enumerated_html_list = beautified_link_source.split("\n")
                counter = 0
                enumerated_html = u""
                for line in enumerated_html_list:
                    counter_line = str(counter)
                    encoded_line = line.decode("utf8")
                    new_line = u"%s: %s"%(counter_line, encoded_line)
                    enumerated_html += u"%s\n"%(new_line)
                    counter += 1

                link['enumerated_html'] = enumerated_html

                raw_js_errors = pyjslint.check_JSLint(beautified_link_source)
                #js_errors = [str(error) for error in raw_js_errors]

                js_errors = []
                for source, full_message in grouped(raw_js_errors[1:], 2):
                    full_message = full_message.strip()

                    if full_message.startswith("Lint"):
                        message = full_message.split(":")[1].strip()
                        line_ref = full_message.split(":")[0].strip()
                        numbers = [int(s) for s in line_ref.split() if s.isdigit()]

                        error = {
                            'lastLine':numbers[0],
                            'lastColumn':numbers[1],
                            'message':full_message,
                            'src':source
                        }
                        print "ERROR"
                        print error
                        js_errors.append(error)

                print "JS ERRORS: %s"%(js_errors)
                total_js_error_count += len(js_errors)
                link['validation'] = {
                    'errors':js_errors
                }
                if len(js_errors) > 0:
                    message = "Warning: Found %s lint errors."%(len(js_errors))
                    link['messages']['warning'].append(message)
            


            #DELETE local file
            #os.unlink(local_file_path)

            
    if total_js_error_count > 0:
        messages['warning'].append("Warning: %s js lint errors found."%(total_js_error_count))             


    #DELETE TMP FOLDER
    try:
        shutil.rmtree('tmp')
    except:
        pass
        

    return links, messages





def store_file_locally(url):

    temp_folder = 'tmp'
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Open the url
    try:
        f = urllib2.urlopen(url)
        local_path = os.path.join(temp_folder, os.path.basename(url))

        # Open our local file for writing
        with open(local_path, "wb") as local_file:
            local_file.write(f.read())

    #handle errors
    except urllib2.HTTPError, e:
        print "HTTP Error:", e.code, url
    except urllib2.URLError, e:
        print "URL Error:", e.reason, url

    return local_path


def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return izip(*[iter(iterable)]*n)