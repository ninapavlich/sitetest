from ..core.retrieve_all_urls import TYPE_INTERNAL
from bs4 import BeautifulSoup, SoupStrainer

def test_basic_page_quality(links, canonical_domain, domain_aliases, messages):
    """
    For each page, make sure there is a unique title and description
    """

    unique_titles = {}
    unique_descriptions = {}

    unique_title_error_count = 0
    unique_description_error_count = 0
    
    for link_url in links:
        link = links[link_url]
        link_type = link['type']
        
        if link_type == TYPE_INTERNAL:
            link_html = link['html']
            if link_html:
                try:
                    soup = BeautifulSoup(link_html)
                    
                    #1 - Test Title
                    try:
                        page_title = soup.title.string
                    except:
                        page_title = ''
                    link['title'] = page_title.strip()

                    if page_title == '':
                        message = "Warning: Page title is missing from <a href='#%s' class='alert-link'>%s</a>."%(link['internal_page_url'], link_url)
                        link['messages']['warning'].append(message)

                    elif page_title not in unique_titles:
                        unique_titles[page_title] = 1
                    else:               
                        unique_titles[page_title] = int(unique_titles[page_title])+1
                        message = "Notice: Page title &ldquo;%s&rdquo; in <a href='#%s' class='alert-link'>%s</a> is not unique."%(page_title, link['internal_page_url'], link_url)
                        link['messages']['info'].append(message)
                        unique_title_error_count += 1

                    #2 - Test Description
                    page_description = None
                    descriptions = soup.findAll(attrs={"name":"description"})
                    for description in descriptions:
                        try:
                            page_description = description['content'].strip()
                            link['description'] = page_description
                        except:
                            pass                        

                    if page_description:

                        if page_description not in unique_descriptions:
                            unique_descriptions[page_description] = 1
                        else:               
                            unique_descriptions[page_description] = int(unique_descriptions[page_description])+1

                            message = "Notice: Page description in <a href='#%s' class='alert-link'>%s</a> is not unique."%(link['internal_page_url'], link_url)
                            link['messages']['info'].append(message)
                            unique_description_error_count += 1

                    else:                       
                        message = "Warning: Page description is missing from <a href='#%s' class='alert-link'>%s</a>."%(link['internal_page_url'], link_url)
                        link['messages']['warning'].append(message)

                    #3 - Test Analytics
                    #TODO
                        
                except:
                    pass

    if unique_title_error_count > 0:
        messages['info'].append("Notice: %s pages were found to non-unique page titles"%(unique_title_error_count))

    if unique_description_error_count > 0:
        messages['info'].append("Notice: %s pages were found to non-unique page descriptions"%(unique_description_error_count))             

    return links, messages

