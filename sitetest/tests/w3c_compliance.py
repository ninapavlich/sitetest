import logging

from w3c_validator.validator import Validator

logger = logging.getLogger('sitetest')


def test_w3c_compliance(set, ignore_validation_errors, max_test_count=20, verbose=False):
    """
    TODO: Test w3c compliance
    Documentation: http://validator.w3.org/docs/api.html
    """

    if verbose:
        logger.debug("Testing W3C Compliance, ignoring %s errors" % (len(ignore_validation_errors)))

    validation_error = set.get_or_create_message_category('validation-error', "Validation errors", 'warning')
    validation_warning = set.get_or_create_message_category('validation-warning', "Validation warnings", 'info')

    # Calculate total number of links to validate
    target_count = 0
    for link_url in set.parsed_links:
        link = set.parsed_links[link_url]
        if link.is_internal and not link.is_media:
            if link.html:
                target_count += 1

    timeout_found_count = 0
    warnings_found_count = 0
    errors_found_count = 0
    validated_count = 0
    for link_url in set.parsed_links:
        link = set.parsed_links[link_url]

        if link.is_internal_html and not link.skip_test:

            link_html = link.html
            link_url = link.url
            if link_html:

                if validated_count < max_test_count:
                    validated_count += 1
                    if verbose:
                        logger.debug("%s/%s" % (validated_count, max_test_count))

                    validator = get_test(link_html)
                    if validator.status != 'Timeout':

                        actual_errors = []
                        actual_warnings = []

                        # Skip validation errors to ignore
                        for error in validator.errors:
                            if error['message'] not in ignore_validation_errors:
                                actual_errors.append(error)

                        # Skip validation warnings to ignore
                        for error in validator.warnings:
                            if error['message'] not in ignore_validation_errors:
                                actual_warnings.append(error)

                        link.validation = {
                            'warnings': actual_warnings,
                            'errors': actual_errors
                        }

                        warnings_found_count += len(actual_warnings)
                        errors_found_count += len(actual_errors)

                        if len(actual_errors) > 0:
                            message = "Found %s validation errors on page <mark>&ldquo;%s&rdquo;</mark>." % (len(actual_errors), link.title)
                            link.add_warning_message(message, validation_error)

                        if len(actual_warnings) > 0:
                            message = "Found %s validation warnings on page <mark>&ldquo;%s&rdquo;</mark>." % (len(actual_warnings), link.title)
                            link.add_info_message(message, validation_warning)

                    else:
                        timeout_found_count += 1
                        message = "Validation was unable to run on this page because it timed out. Please manually check the W3C Validation link in the 'Tools' tab."
                        link.add_warning_message(message)

    # if warnings_found_count > 0:
    #     set.add_info_message("%s validation warnings found"%(warnings_found_count), validation_warning, warnings_found_count)

    # if errors_found_count > 0:
    #     set.add_warning_message("%s validation errors found"%(errors_found_count), validation_error, errors_found_count)

    # if timeout_found_count > 0:
    #     set.add_warning_message("%s pages were unable to validate because they timed out. Please manually check those pages using the W3C Validation link in the 'Tools' tab."%(timeout_found_count), timeout_found_count)


def get_test(link_html, attempt=0):
    max_attempts = 10

    validator = Validator()
    validator.validate_source(link_html)
    if validator.status != 'Timeout':
        return validator
    else:
        if attempt < max_attempts:
            return get_test(link_html, attempt + 1)
        else:
            return validator
