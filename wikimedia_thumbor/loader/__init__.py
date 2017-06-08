def are_request_dimensions_valid(context, dimensions_header):
    '''
    Checks the current request against the X-Content-Dimensions header.

    The header is made of a /-separated list of page ranges by width/height dimension pairs.
    Page ranges can be a single page number, a range with lower and upperbound or a list
    of either/both.

    Example "complex" header:
    1667x2338:1/1575x2267:2/2350x3317:3-4/1438x2250:5/1413x2204:6,9/1425x2300:7/1433x2204:8

    Example header for a single page document:
    1667x2338:1

    If no dimensions information for the request's page is found, or if the
    X-Content-Dimensions header is malformed, we assume that the request is valid.
    '''
    try:
        page = context.request.page
    except AttributeError:
        page = 1

    dimensions_limits = dimensions_header.split('/')

    for page_ranges_by_dimensions in dimensions_limits:
        parts = page_ranges_by_dimensions.split(':')

        if len(parts) != 2:
            return True

        dimensions = parts[0].split('x')
        try:
            width = int(dimensions[0])
        except ValueError:
            return True

        pages = parts[1]
        page_ranges = pages.split(',')

        # Iterate over list of pages and page ranges
        for page_range in page_ranges:
            bound_pages = page_range.split('-')

            if len(bound_pages) == 1:
                # Single page
                try:
                    if int(bound_pages[0]) == page:
                        if context.request.width >= width:
                            return False
                except ValueError:
                    return True
            else:
                try:
                    lower_bound = int(bound_pages[0])
                    upper_bound = int(bound_pages[1])
                except ValueError:
                    return True

                # Ranges, check if current page is in it
                if page >= lower_bound and page <= upper_bound:
                    if context.request.width >= width:
                        return False

    return True
