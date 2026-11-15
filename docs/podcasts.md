---
layout: default
title: Podcasts
---

# Podcasts

Horizon can collect podcast episodes with public written transcripts, evaluate
them with your configured AI model, and include a substantial localized summary
in the normal digest. This source is opt-in: `sources.podcast` is empty by default.

The first version reads publisher-declared transcript links in RSS feeds. It does
not download audio, perform speech recognition, or search for unofficial copies.
A podcast's presence in Apple Podcasts or Spotify does not by itself make a
transcript available to Horizon.

## Configure a Feed

Merge this fragment into your existing configuration; keep your AI and delivery
settings. The example uses the public Talk Python To Me feed, which publishes
WebVTT transcript links. Transcript availability may vary by episode.

```json
{
  "sources": {
    "podcast": [
      {
        "name": "Talk Python To Me",
        "url": "https://talkpython.fm/episodes/rss",
        "enabled": true,
        "profile": "podcast",
        "category": "podcasts",
        "max_items": 3,
        "max_transcript_chars": 200000
      }
    ]
  }
}
```

Then run Horizon normally:

```bash
uv run horizon
```

This uses the existing collection window, filtering, digest quotas, configured
languages, and delivery channels. To inspect collection before making model
requests, use the existing MCP/helper fetch stage with source type `podcast`.
There is no separate podcast scheduler or rolling seven-day queue in this version.

To keep distinct interviews that discuss the same topic, you can disable topic
merging for this profile in runtime configuration:

```json
{
  "processing": {
    "profile_settings": {
      "podcast": {
        "topic_dedup": false
      }
    }
  }
}
```

This leaves ordinary duplicate handling in place. Configure score thresholds and
digest quotas separately to control which episodes appear and how many to keep.

| Feed field | Default | Meaning |
| --- | --- | --- |
| `name` | Required | Label used in source diagnostics and episode metadata |
| `url` | Required | Public RSS feed URL |
| `enabled` | `true` | Whether to collect this feed |
| `profile` | `"podcast"` | Processing profile; keep the built-in value for whole-transcript processing |
| `category` | Unset | Optional category for digest quota grouping |
| `max_items` | `10` | Maximum eligible episodes considered per feed, from 1 to 100 |
| `max_transcript_chars` | `200000` | Reject longer extracted transcripts; allowed range 1,000–500,000 characters |

Episode selection uses the original publication time, rather than a later feed
update. Missing publication times and future-dated episodes are not admitted.
`max_items` is a collection limit, not a promise that this many episodes will
survive transcript validation, scoring, or digest filtering.

## Transcript Availability

Each RSS item must declare a
[`podcast:transcript`](https://podcasting2.org/docs/podcast-namespace/tags/transcript)
link. Horizon supports these declared formats:

| Declared type | Processing |
| --- | --- |
| `text/plain` | Read UTF-8 transcript text |
| `text/vtt` | Read WebVTT captions, retaining time markers |
| `application/x-subrip` or `text/srt` | Read SRT captions, retaining time markers |
| `text/html` | Extract text with the included `trafilatura` dependency |

An HTML link must be explicitly declared as a transcript by the publisher; an
episode page or show-notes link alone is insufficient. The Podcast Namespace
also permits JSON transcripts, but this version does not parse them. When an
episode declares alternatives, Horizon tries up to three supported links.

Public examples include [Talk Python To Me](https://talkpython.fm/episodes/rss)
(WebVTT) and [Practical AI](https://changelog.com/practicalai/feed) (HTML).
These are examples of the feed
contract, not a required subscription list or an endorsement of every episode.

Horizon retains the episode URL, feed name, GUID, transcript URL, and transcript
format. A `complete` transcript status means the entire declared resource was
fetched and extracted; it cannot establish whether a publisher omitted material
from the original recording. Speaker names and time markers can only be retained
when the source supplies them.

Missing, unsupported, empty, oversized, or inaccessible transcripts produce
named fetch diagnostics. Other episodes and feeds can still succeed. Horizon
does not substitute a short episode description and present it as a full reading.
Feed responses are limited to 8 MiB and transcript responses to 4 MiB; individual
requests have a 20-second timeout. Public URL checks also apply to redirects.

## Whole-Transcript Processing

The built-in `podcast` profile uses `content.long_form`. Before scoring, Horizon
divides the transcript into bounded chunks and asks the configured model to
extract claims, reasons, examples, and qualifications from every chunk. These
notes preserve source locations and speaker attribution when available. Analysis
and enrichment then use the combined notes instead of sampling only the opening
of the episode.

The profile's input settings are:

```json
{
  "content": {
    "analysis_max_chars": 32000,
    "enrichment_max_chars": 32000,
    "long_form": {
      "chunk_chars": 12000,
      "max_chunks": 24
    }
  }
}
```

`chunk_chars` accepts 1,000–32,000 characters and `max_chunks` accepts 1–64.
Chunks prefer paragraph boundaries, so the actual count can exceed a simple
character-count division. The notes must fit both stage budgets, with at least
500 characters of note budget per chunk. Transcripts exceeding the chunk limit
fail before extraction model calls; incomplete extraction does not fall back to
prefix-only scoring or a purported full summary. Chunk coverage describes what
was processed, not a guarantee that a model's interpretation is correct.

Validated notes and coverage are stored in the item's `metadata.long_form`.
They are reused by enrichment and by resumed stages that retain the item. The
cache is tied to the source text, profile, and model, so changed inputs require
fresh extraction. The extraction layer allows at most two model attempts per
chunk for the same cached input; the AI client's own transport retries can still
apply. A completely fresh collection does not share a global transcript cache.

Long-form processing adds model calls and cost before the normal score filter.
Start with a small `max_items`, and choose a `chunk_chars` value appropriate for
your model's context window. Character limits are not token or currency budgets.
No additional speech-to-text service or API key is required.

The profile prioritizes concrete first-hand insight, supporting reasoning and
examples, and useful qualifications. Guest fame alone is insufficient for a high
score. Summaries attribute opinions and predictions to their speakers, omit
sponsor copy, and avoid reproducing long passages of the transcript. The target
is approximately 600–800 English words or 900–1,200 Chinese characters, adapted
to the configured language and the actual substance available. Customize the
length and structure in `profiles/podcast/enrichment.md`; thresholds and quotas
remain runtime settings.

## Limits

- Feeds without declared public transcripts need another ingestion strategy;
  ordinary RSS show notes are not supported as a substitute.
- Authentication, paywall access, audio transcription, and platform-specific
  browser scraping are not included.
- There is no new per-episode publication history or cross-platform identity
  service. Existing Horizon duplicate handling still applies.
- Follow publishers' terms and transcript licenses when retaining or publishing
  material. The digest is a summary with links, not a transcript redistribution
  service.
