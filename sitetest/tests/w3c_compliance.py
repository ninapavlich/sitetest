from ..core.retrieve_all_urls import TYPE_INTERNAL
from w3c_validator.validator import Validator

def test_w3c_compliance(links, canonical_domain, domain_aliases, messages, ignore_validation_errors, verbose=False):
    """
    TODO: Test w3c compliance
    Documentation: http://validator.w3.org/docs/api.html
    """

    if verbose:
        print "Testing W3C Compliance, ignoring the following errors %s"%(ignore_validation_errors)

    timeout_found_count = 0
    warnings_found_count = 0
    errors_found_count = 0
    for link_url in links:
        link = links[link_url]
        link_type = link['type']
        
        if link_type == TYPE_INTERNAL:
            link_html = link['html']
            link_url = link['url']
            if link_html:
                

                validator = get_test(link_html)
                #print "validator? %s"%(validator)
                if validator.status != 'Timeout':
                    
                    

                    actual_errors = []
                    actual_warnings = []

                    #Skip validation errors to ignore
                    for error in validator.errors:
                        #print 'test %s for %s: %s'%(error['message'], ignore_validation_errors, (error['message'] in ignore_validation_errors))
                        if error['message'] not in ignore_validation_errors:
                            actual_errors.append(error)

                    

                    #Skip validation warnings to ignore
                    for error in validator.warnings:
                        if error['message'] not in ignore_validation_errors:
                            actual_warnings.append(error)

                        

                    link['validation'] = {
                        'warnings':actual_warnings,
                        'errors':actual_errors
                    }

                    warnings_found_count += len(actual_warnings)
                    errors_found_count += len(actual_errors)

                    if validator.error_count > 0:
                        message = "Warning: Found %s validation errors on page %s."%(len(actual_errors), link_url)
                        link['messages']['warning'].append(message)

                    if validator.warning_count > 0:
                        message = "Notice: Found %s validation warnings on page %s."%(len(actual_warnings), link_url)
                        link['messages']['info'].append(message)

                    enumerated_html_list = link_html.split("\n")
                    counter = 0
                    enumerated_html = ''
                    for line in enumerated_html_list:
                        new_line = "<strong>%s:</strong> %s"%(counter, line)
                        enumerated_html += "%s\n"%(new_line)
                        counter += 1

                    link['enumerated_html'] = enumerated_html
                else:
                    timeout_found_count += 1
                    message = "Warning: Validation was unable to run on this page because it timed out. Please manually check the W3C Validation link in the 'Tools' tab."
                    link['messages']['warning'].append(message)


    if warnings_found_count > 0:
        messages['info'].append("Notice: %s validation warnings found"%(warnings_found_count))

    if errors_found_count > 0:
        messages['warning'].append("Warning: %s validation errors found"%(errors_found_count))  

    if timeout_found_count > 0:
        messages['warning'].append("Warning: %s pages were unable to validate because they timed out. Please manually check those pages using the W3C Validation link in the 'Tools' tab."%(timeout_found_count))             



    return links, messages

def get_test(link_html, attempt=0):
    max_attempts = 10
    # if attempt > 0:
    #     print 'test attempt %s'%(attempt)

    validator = Validator()
    validator.validate_source(link_html)
    if validator.status != 'Timeout':
        return validator
    else:
        if attempt < max_attempts:
            return get_test(link_html, attempt+1)
        else:
            return validator