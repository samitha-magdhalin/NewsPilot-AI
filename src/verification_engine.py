from datetime import datetime, timezone, timedelta
from .data_models import VerificationStatus, Claim
from .source_independence import assess_independence

def assess_story(story, primary_source_domains=None, freshness_hours=168):
    primary_source_domains=set(primary_source_domains or [])
    arts=story.related_articles; now=datetime.now(timezone.utc)
    dates=[a.published_at for a in arts if a.published_at]
    if dates and max(dates)<now-timedelta(hours=freshness_hours): status=VerificationStatus.OUTDATED
    elif not arts: status=VerificationStatus.INSUFFICIENT_EVIDENCE
    elif any(c.status==VerificationStatus.CONFLICTING_REPORTS for c in story.claims): status=VerificationStatus.CONFLICTING_REPORTS
    elif any(a.publisher_domain in primary_source_domains for a in arts): status=VerificationStatus.PRIMARY_SOURCE_SUPPORTED
    elif len({a.publisher_domain for a in arts if a.publisher_domain})>=2 and not assess_independence(arts)['syndication_suspected']:
        status=VerificationStatus.MULTI_SOURCE_SUPPORTED
    elif len(arts)==1: status=VerificationStatus.SINGLE_SOURCE
    else: status=VerificationStatus.INSUFFICIENT_EVIDENCE
    story.verification_status=status
    story.evidence_coverage=round(min(1.0, len({a.publisher_domain for a in arts})/3),2) # coverage, not truth probability
    if not story.claims:
        story.limitations.append('No claim-level assessment has been completed; story-level status reflects source coverage only.')
    story.limitations.append('Source-domain count is not proof of independent investigations.')
    return {'status':status.value,'claims':[c.model_dump(mode='json') for c in story.claims],
      'sources':[{'publisher':a.publisher_name,'url':a.canonical_url,'published_at':a.published_at.isoformat() if a.published_at else None} for a in arts],
      'source_independence':assess_independence(arts),'evidence_coverage':story.evidence_coverage,
      'coverage_note':'Evidence coverage is a source-availability measure, not probability of truth.',
      'limitations':story.limitations,'verified_at':now.isoformat()}
