# SPDX-License-Identifier: Apache-2.0
"""Build an evidence-backed AI briefing from mixed document formats."""

from html import escape
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen

from sentence_transformers import SentenceTransformer
import tika_ape


class EvidenceCopilot:
    """Turns heterogeneous documents into cited semantic-search evidence."""

    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    sources = (
        {
            'fileName': 'attention-is-all-you-need.pdf',
            'format': 'PDF',
            'title': 'Attention Is All You Need',
            'url': 'https://arxiv.org/pdf/1706.03762',
        },
        {
            'fileName': 'ai-risk-management-framework.html',
            'format': 'HTML',
            'title': 'NIST AI Risk Management Framework',
            'url': 'https://www.nist.gov/itl/ai-risk-management-framework',
        },
        {
            'fileName': 'machine-learning-glossary.html',
            'format': 'HTML',
            'title': 'Google Machine Learning Glossary',
            'url': 'https://developers.google.com/machine-learning/glossary',
        },
    )
    questions = (
        'Why did transformers become important for language modeling?',
        'What risks should an organization manage when adopting AI?',
        'How do embeddings help retrieve relevant information?',
    )

    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)
        self.assets_path = self.root_path / 'assets'
        self.output_path = self.root_path / 'output'

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 820) -> list[str]:
        paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
        chunks = []
        current_chunk = ''

        for paragraph in paragraphs:
            candidate = f'{current_chunk}\n\n{paragraph}'.strip()
            if len(candidate) <= chunk_size:
                current_chunk = candidate
                continue

            chunks.append(current_chunk)
            current_chunk = paragraph

        chunks.append(current_chunk)

        return [chunk for chunk in chunks if len(chunk) >= 120]

    @staticmethod
    def _render_evidence(result: dict[str, object]) -> str:
        evidence_items = ''.join(
            f'''<article class="evidence">
              <div class="evidenceHeader">
                <span>{escape(match['title'])}</span>
                <strong>{match['score']:.1%} relevance</strong>
              </div>
              <p>{escape(match['excerpt'])}</p>
              <small>{escape(match['format'])} · chunk {match['chunkNumber']}</small>
            </article>'''
            for match in result['matches']
        )

        return f'''<section class="question">
          <div class="questionLabel">Question</div>
          <h2>{escape(result['question'])}</h2>
          <p class="answer">The strongest evidence comes from {escape(result['matches'][0]['title'])}. Review the cited passages below before drawing a conclusion.</p>
          <div class="evidenceGrid">{evidence_items}</div>
        </section>'''

    def _download_sources(self) -> None:
        self.assets_path.mkdir(parents=True, exist_ok=True)

        for source in self.sources:
            target_path = self.assets_path / source['fileName']
            request = Request(
                source['url'],
                headers={'User-Agent': 'tika-ape-evidence-copilot/0.1'},
            )

            with urlopen(request) as response, target_path.open('wb') as target_file:
                shutil.copyfileobj(response, target_file)

    def _build_corpus(self) -> list[dict[str, object]]:
        chunks = []

        for source in self.sources:
            source_path = self.assets_path / source['fileName']
            text = tika_ape.extract_text(source_path)

            for chunk_number, chunk in enumerate(self._chunk_text(text), start=1):
                chunks.append({
                    **source,
                    'chunkNumber': chunk_number,
                    'text': chunk,
                })

        return chunks

    def _answer_questions(self, chunks: list[dict[str, object]]) -> list[dict[str, object]]:
        model = SentenceTransformer(self.model_name)
        corpus_vectors = model.encode(
            [chunk['text'] for chunk in chunks],
            normalize_embeddings=True,
        )
        question_vectors = model.encode(self.questions, normalize_embeddings=True)
        answers = []

        for question, question_vector in zip(self.questions, question_vectors):
            scores = question_vector @ corpus_vectors.T
            top_indexes = scores.argsort()[-3:][::-1]
            matches = []

            for index in top_indexes:
                chunk = chunks[int(index)]
                matches.append({
                    'chunkNumber': chunk['chunkNumber'],
                    'excerpt': ' '.join(chunk['text'].split())[:520],
                    'format': chunk['format'],
                    'score': float(scores[index]),
                    'title': chunk['title'],
                })

            answers.append({'question': question, 'matches': matches})

        return answers

    def _render_report(
        self,
        chunks: list[dict[str, object]],
        answers: list[dict[str, object]],
    ) -> str:
        question_sections = ''.join(self._render_evidence(answer) for answer in answers)
        document_items = ''.join(
            f'<li><strong>{escape(source["format"])}</strong>{escape(source["title"])}</li>'
            for source in self.sources
        )

        return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Evidence Copilot</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: #f0f4ff; background: #070b17; }}
    header {{ padding: 80px max(7vw, 28px) 62px; background: radial-gradient(circle at 78% 10%, #8234b3 0, #1f2355 33%, #070b17 66%); }}
    .eyebrow {{ color: #f3a4ff; font-size: .75rem; font-weight: 800; letter-spacing: .17em; text-transform: uppercase; }}
    h1 {{ max-width: 860px; margin: 15px 0; font-size: clamp(3rem, 7vw, 6.8rem); letter-spacing: -.07em; line-height: .9; }}
    .lead {{ max-width: 800px; color: #c1c8e5; font-size: 1.13rem; line-height: 1.7; }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 30px; }}
    .stat {{ min-width: 160px; padding: 16px 18px; border: 1px solid #754c9b; border-radius: 13px; background: #161939aa; }}
    .stat span {{ display: block; color: #a9afd2; font-size: .72rem; letter-spacing: .09em; text-transform: uppercase; }}
    .stat strong {{ display: block; margin-top: 4px; font-size: 1.4rem; }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 46px max(4vw, 22px) 88px; }}
    .sources {{ padding: 22px; border: 1px solid #303866; border-radius: 16px; background: #10162b; }}
    .sources h2 {{ margin: 0 0 13px; font-size: 1rem; }}
    .sources ul {{ display: flex; flex-wrap: wrap; gap: 9px; margin: 0; padding: 0; list-style: none; }}
    .sources li {{ padding: 8px 11px; border-radius: 9px; background: #1b2543; color: #c7d0eb; font-size: .85rem; }}
    .sources strong {{ margin-right: 8px; color: #f2a8ff; font-size: .7rem; letter-spacing: .08em; }}
    .question {{ margin-top: 35px; padding-top: 8px; }}
    .questionLabel {{ color: #e68bff; font-size: .72rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }}
    .question h2 {{ margin: 8px 0; font-size: clamp(1.6rem, 3vw, 2.4rem); letter-spacing: -.04em; }}
    .answer {{ margin: 0 0 18px; color: #aeb9d9; line-height: 1.6; }}
    .evidenceGrid {{ display: grid; gap: 14px; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .evidence {{ padding: 19px; border: 1px solid #29355c; border-radius: 14px; background: linear-gradient(145deg, #121b34, #0d1226); }}
    .evidenceHeader {{ display: flex; justify-content: space-between; gap: 12px; color: #cbd6f4; font-size: .82rem; font-weight: 700; }}
    .evidenceHeader strong {{ color: #9ee7ca; white-space: nowrap; }}
    .evidence p {{ min-height: 138px; color: #d8def0; font-family: Georgia, serif; font-size: .96rem; line-height: 1.62; }}
    .evidence small {{ color: #9ca8c9; }}
    footer {{ padding: 28px; color: #8894b8; border-top: 1px solid #26335b; text-align: center; font-size: .85rem; }}
    @media (max-width: 860px) {{ .evidenceGrid {{ grid-template-columns: 1fr; }} .evidence p {{ min-height: 0; }} }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Tika APE × local embedding model</div>
    <h1>Evidence Copilot</h1>
    <p class="lead">An AI-ready document pipeline: Tika opens mixed formats, a local embedding model finds semantic evidence, and the result keeps every answer tied to the exact source passage.</p>
    <div class="stats">
      <div class="stat"><span>Source documents</span><strong>{len(self.sources)}</strong></div>
      <div class="stat"><span>Evidence chunks</span><strong>{len(chunks)}</strong></div>
      <div class="stat"><span>Embedding model</span><strong>MiniLM</strong></div>
      <div class="stat"><span>Cloud API calls</span><strong>0</strong></div>
    </div>
  </header>
  <main>
    <section class="sources"><h2>Corpus</h2><ul>{document_items}</ul></section>
    {question_sections}
  </main>
  <footer>Generated locally by <code>tika_ape</code> and <code>{escape(self.model_name)}</code>. The evidence passages, not an opaque model answer, are the product.</footer>
</body>
</html>'''

    def build(self) -> tuple[Path, Path, int]:
        self._download_sources()

        chunks = self._build_corpus()
        answers = self._answer_questions(chunks)
        self.output_path.mkdir(parents=True, exist_ok=True)

        report_path = self.output_path / 'index.html'
        evidence_path = self.output_path / 'evidence.json'
        report_path.write_text(self._render_report(chunks, answers), encoding='utf-8')
        evidence_path.write_text(json.dumps(answers, indent=2), encoding='utf-8')

        return report_path, evidence_path, len(chunks)


def main() -> None:
    example_path = Path(__file__).resolve().parent
    copilot = EvidenceCopilot(example_path)
    report_path, evidence_path, chunk_count = copilot.build()

    print(f'Evidence Copilot report: {report_path}')
    print(f'Evidence records: {evidence_path}')
    print(f'Embedded evidence chunks: {chunk_count}')


if __name__ == '__main__':
    main()
