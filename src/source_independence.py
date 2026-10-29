def assess_independence(articles):
    domains={a.publisher_domain for a in articles if a.publisher_domain}
    # Domain diversity is only a proxy; it does not prove independent reporting.
    syndicated=any(any(marker in a.title.lower() for marker in ('associated press','reuters','ap news')) for a in articles)
    return {'distinct_domains':len(domains),'domains':sorted(domains),'independence':'uncertain' if len(domains)>1 else 'not_established',
            'syndication_suspected':syndicated,
            'note':'Different domains do not prove independent reporting; syndicated copies must not be counted as independent confirmations.'}
