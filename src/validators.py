def validate_citations(source_ids, registry):
    return [sid for sid in source_ids if sid in registry]
def safe_filename(name):
    import re
    value=re.sub(r'[^a-zA-Z0-9._-]+','_',name).strip('._')
    return (value or 'newspilot_export')[:100]
