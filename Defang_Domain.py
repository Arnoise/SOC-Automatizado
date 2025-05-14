import re

def defang_domain(url):
    """
    Function to defang a URL by replacing periods with [.] and modifying common parts
    to prevent automatic access.
    """
    # Replace the period `.` with `[.]`
    defanged_url = url.replace('.', '[.]')
    
    # Optionally replace other parts of the URL
    defanged_url = defanged_url.replace('://', '[://]')  # Defang "://"
    defanged_url = defanged_url.replace('www.', '[www.]')  # Defang "www."
    
    return defanged_url

# Test the function
url = "$html_to_json.#.domain"
defanged_url = defang_domain(url)
print(f"{defanged_url}")
