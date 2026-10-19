"""Create a new local archival Git repository from the reviewed import plan."""
from pathlib import Path
from html.parser import HTMLParser
import ast
import collections
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'competitive-tf2-staged'
REPO.mkdir(exist_ok=False)
PLAN = json.loads((ROOT / 'archive-plan.json').read_text())
URL = PLAN['source_url']
CAPTURED = dt.datetime.fromtimestamp((ROOT / 'shared-chat.html').stat().st_mtime, dt.timezone.utc).isoformat()
ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
           GIT_AUTHOR_NAME='ChatGPT conversation archive', GIT_AUTHOR_EMAIL='source@archive.invalid',
           GIT_COMMITTER_NAME='Codex archive import', GIT_COMMITTER_EMAIL='import@archive.invalid')
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'):
    ENV.pop(key, None)


def git(*args, date=None):
    env = dict(ENV)
    if date:
        env['GIT_AUTHOR_DATE'] = date
    return subprocess.run(['git', '-C', str(REPO), '-c', 'core.hooksPath=/dev/null',
                           '-c', 'core.fsmonitor=false', '-c', 'commit.gpgsign=false',
                           *args], env=env, check=True, text=True, capture_output=True).stdout


def write(rel, content):
    target = REPO / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content)
    target.chmod(0o644)


def jwrite(rel, content):
    write(rel, json.dumps(content, ensure_ascii=False, indent=2) + '\n')


template = ROOT / 'empty-git-template'
template.mkdir(exist_ok=True)
git('init', '--initial-branch=main', '--template=' + str(template))
git('config', '--local', 'core.hooksPath', '/dev/null')
git('config', '--local', 'core.fsmonitor', 'false')
git('config', '--local', 'commit.gpgsign', 'false')
git('config', '--local', 'user.name', 'Codex archive import')
git('config', '--local', 'user.email', 'import@archive.invalid')
records = []
hash_checks = 0
syntax_checks = 0
for e in PLAN['events']:
    clean = {k: v for k, v in e.items() if k != 'writes'}
    clean['writes'] = []
    for w in e['writes']:
        data = (ROOT / w['payload']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == w['sha256']
        assert len(data) == w['bytes']
        write(w['repo_path'], data)
        hash_checks += 1
        wc = {k: v for k, v in w.items() if k != 'payload'}
        if w['repo_path'].endswith('.py'):
            ast.parse(data.decode('utf-8'))
            syntax_checks += 1
            wc['static_syntax'] = 'parsed_without_execution'
        clean['writes'].append(wc)
    date = dt.datetime.fromtimestamp(e['source_timestamp'], dt.timezone.utc).isoformat()
    event_path = f".provenance/events/{e['sequence']:04d}-{e['message_id']}.json"
    jwrite(event_path, clean)
    git('add', '--all')
    paths = [w['repo_path'] for w in clean['writes']]
    subject = f"archive {e['sequence']:04d}: " + ', '.join(paths[:2]) + (' and others' if len(paths) > 2 else '')
    types = ', '.join(sorted(set(w['status'] for w in clean['writes'])))
    body = (f'{subject}\n\nImport of available conversation material; no recovered code executed.\n\n'
            f'Source-URL: {URL}\nSource-Message: {e["message_id"]}\n'
            f'Source-Sequence: {e["sequence"]}\nSource-Time: {date}\nContent-Status: {types}\n')
    git('commit', '--no-verify', '-F', '-', date=date) if False else None
    subprocess.run(['git', '-C', str(REPO), '-c', 'core.hooksPath=/dev/null',
                    '-c', 'core.fsmonitor=false', '-c', 'commit.gpgsign=false',
                    'commit', '--no-verify', '--file=-'], input=body, text=True,
                   env=dict(ENV, GIT_AUTHOR_DATE=date), check=True, capture_output=True)
    clean['commit'] = git('rev-parse', 'HEAD').strip()
    records.append(clean)

# Source snapshots and original command text are evidence only, never executed.
write('.provenance/source/shared-chat.html.txt', (ROOT / 'shared-chat.html').read_bytes())
route = json.loads((ROOT / 'share-route.json').read_text())
jwrite('.provenance/source/conversation.json', route['serverResponse']['data'])
write('.provenance/source/conversation-visible.md', (ROOT / 'conversation-visible.md').read_bytes())
for p in sorted((ROOT / 'inspection').glob('*-assistant.txt')):
    write('.provenance/source/messages/' + p.name, p.read_bytes())
for p in sorted((ROOT / 'inspection').glob('*-user.txt')):
    write('.provenance/source/messages/' + p.name, p.read_bytes())
write('.provenance/tools/prepare_archive.py', (ROOT / 'prepare_archive.py').read_bytes())
write('.provenance/tools/build_repository.py', Path(__file__).read_bytes())
write('.provenance/PROGRESS.md', (ROOT / 'PROGRESS.md').read_bytes())

all_writes = [w for e in records for w in e['writes']]
paths = collections.Counter(w['repo_path'] for w in all_writes)
types = collections.Counter(w['status'] for w in all_writes)
references = []
for original, sequences in sorted(PLAN['named_references'].items()):
    matches = [dict(sequence=e['sequence'], commit=e['commit'], repo_path=w['repo_path'], status=w['status'])
               for e in records for w in e['writes'] if w['original_path'] == original]
    is_dir = any(w['original_path'].startswith(original.rstrip('/') + '/') for w in all_writes)
    references.append({'original_path': original, 'messages': sorted(set(sequences)),
                       'status': 'archived' if matches else ('directory_reference' if is_dir else 'unavailable'),
                       'revisions': matches})
jwrite('.provenance/revisions.json', records)
jwrite('.provenance/gaps.json', PLAN['gaps'])
jwrite('.provenance/references.json', references)
jwrite('.provenance/capture.json', {
    'source_url': URL, 'title': PLAN['title'], 'captured_at_utc': CAPTURED,
    'computer': 'NEBULOSA-2.local', 'http_status': 200,
    'source_bytes': (ROOT / 'shared-chat.html').stat().st_size,
    'source_sha256': hashlib.sha256((ROOT / 'shared-chat.html').read_bytes()).hexdigest(),
    'nodes': PLAN['nodes'], 'code_messages': 89, 'redacted_tool_nodes': 213,
    'direct_conversation_search_used': False,
    'browser': 'Unavailable: Mac locked; explicit public share downloaded instead.',
    'engineering_guidance': [
        '/Users/marcelofcandido/.codex/plugins/cache/claude-cowork/engineering/1.1.0/README.md',
        '/Users/marcelofcandido/.codex/plugins/cache/claude-cowork/engineering/1.1.0/skills/documentation/SKILL.md',
        '/Users/marcelofcandido/.codex/plugins/cache/claude-cowork/engineering/1.1.0/skills/code-review/SKILL.md'],
    'policy': 'Archive only; recovered installers, patch scripts, tests and configurations were never run.',
    'dates': 'New import commits. AuthorDate preserves source-message UTC time; CommitDate records the import. These are not original Git commits.',
    'classification': dict(types), 'artifact_paths': len(paths), 'revision_records': len(all_writes),
    'validation': {'sha256_revision_checks': hash_checks, 'python_static_parses': syntax_checks,
                   'recovered_code_executions': 0},
})

rows = ['| Caminho no repositório | Registros de revisão |', '|---|---:|']
rows += [f'| `{path}` | {count} |' for path, count in paths.items()]
timeline = ['| Fonte | Data UTC | Commit | Conteúdo |', '|---|---|---|---|']
for e in records:
    date = dt.datetime.fromtimestamp(e['source_timestamp'], dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    timeline.append(f"| {e['sequence']:04d} | {date} | `{e['commit'][:12]}` | " + ', '.join('`' + w['repo_path'] + '`' for w in e['writes']) + ' |')
write('REVISIONS.md', '# Revisões recuperadas\n\nCada commit importa uma etapa da fonte. O manifesto registra mensagem, caminho original, classificação, receita e SHA-256.\n\n'
      + '\n'.join(timeline) + '\n\n' + '\n'.join(rows) + '\n')
write('GAPS.md', '''# Lacunas da fonte

Este arquivo registra ausências; nenhum arquivo vazio foi criado para representar conteúdo desconhecido.

- **v1.4.0:** anunciada na resposta 468, mas a última edição de código disponível define `1.3.1`. Não há bytes completos de v1.4.0 nem a alteração intermediária correspondente.
- **v1.5.0:** a alteração 544 depende dessa base v1.4.0. Foi preservado um candidato em `reconstructions/incomplete-v1.5.0/`, obtido aplicando somente os trechos disponíveis à última base recuperável. A substituição de versão não encontra correspondência; o código conserva `1.3.1`. O candidato e seus testes não representam anexos originais verificados.
- **Duas variantes v1.3.0:** as mensagens 325 e 398 alteram uma base v1.2.0 de formas diferentes. Ambas estão no histórico. A escolha da base de 398 é uma inferência documentada, sustentada pelos textos antigos exigidos e pelo nome do backup em 359.
- **Galeria:** há gerador para `TF2_HUD_Gallery.html`, reconstruído estaticamente. O link da resposta usa `TF2_HUD_Visual_Comparison.html`, cujo conteúdo e eventual renomeação não estão disponíveis. Não foi criado um arquivo com esse nome por suposição.
- **Reparo das imagens:** aparecem a reclamação e uma tentativa de buscar imagens, mas os bytes baixados e a galeria reparada estão ausentes. URLs atuais não foram usadas para inventar cópias históricas.
- **Anexos e resultados ocultos:** há 213 mensagens com resultados de ferramentas redigidos. Links `sandbox:/mnt/data/...` não fornecem os bytes de anexos pela página pública. Logs, JSONs de consultas, ZIPs, imagens e backups cujo conteúdo não está visível constam em `.provenance/references.json` como indisponíveis.
- **Arquivos gerados:** configurações finais `autoexec.cfg`, `modules.cfg`, `setup_hook.cfg`, migrações de classes, manifests e fixtures dependem dos arquivos de entrada ou da execução original. Os templates permanecem no código; somente os blocos explicitamente fornecidos no guia foram extraídos como CFGs. O bloco opcional de Medic está em `alternatives/medic/`.
- **Pedido final:** a conversa termina com a solicitação de tratar dependências externas dos HUDs e uma intenção de atualizar. Nenhuma nova revisão concluída está disponível.

O Mac estava bloqueado, impedindo acesso ao navegador autenticado. A recuperação usou somente o link público explicitamente fornecido. Não houve busca direta de conversas. Os IDs do compartilhamento e da conversa original não foram confundidos.
''')
write('reconstructions/incomplete-v1.5.0/README.md', '''# Candidato incompleto, não um anexo original

Estes arquivos resultam de alterações de texto das mensagens 544 e 548 aplicadas à última base recuperável (v1.3.1 e seus testes). A base v1.4.0 esperada não está disponível. A troca `1.4.0 → 1.5.0` não corresponde ao texto recuperado; nenhum número de versão foi inventado.

Consulte `../../GAPS.md` e as receitas em `../../.provenance/revisions.json`. Nenhum destes arquivos foi executado, importado ou testado em TF2.
''')
write('README.md', f'''# TF2 Competitive Setup Linux — arquivo da conversa

Repositório Git **local** de preservação de [TF2 Competitive Setup Linux]({URL}), recuperado em {CAPTURED}. Não é uma instalação de TF2.

Foram preservados **27 caminhos de artefatos**, com **42 registros de revisão** em **22 commits cronológicos de conteúdo** e um commit final de documentação/evidências. Os registros se dividem em **18 conteúdos literais disponíveis**, **22 reconstruções estáticas** e **2 candidatos incompletos**. Cópias com bytes idênticos são identificadas pelos mesmos hashes; registros não significam 42 versões distintas.

O instalador na raiz possui **8 estados recuperáveis**: original sem `SCRIPT_VERSION`, ajuste inicial, v1.1.0, duas revisões v1.2.0, duas variantes v1.3.0 e v1.3.1. As oito revisões representam novos commits de importação. **A fonte não permite recuperar exatamente v1.4.0 e v1.5.0**, nem o HTML anunciado como `TF2_HUD_Visual_Comparison.html`. Veja [GAPS.md](GAPS.md).

Conteúdos literais vieram de heredocs/blocos fornecidos no chat; isso não equivale a verificar os bytes de um anexo original. Reconstruções usam somente extração de literais e edições de texto revisadas. **Nenhum instalador, script de alteração, teste ou CFG recuperado foi executado.** A validação verifica hashes e sintaxe por análise estática.

## Consultar o histórico

```bash
git status --short
git log --reverse --format='%h %aI %s'
git log --follow -- setup_tf2_bazzite.py
git show COMMIT:setup_tf2_bazzite.py
```

[REVISIONS.md](REVISIONS.md) lista os commits e arquivos. `.provenance/revisions.json` liga cada registro à mensagem, caminho original, SHA-256 e receita. `.provenance/source/` preserva a captura pública e os textos originais, como dados. O HTML bruto termina em `.txt` para evitar execução acidental da página. `.provenance/references.json` distingue arquivos arquivados de referências sem conteúdo disponível.

Os diretórios `/mnt/data/` da conversa foram mapeados relativamente à raiz, mantendo nomes e subpastas. Para preservar simultaneamente `TF2_HUD_UPDATE_README.md` e `TF2_HUD_Update_README.md` em um disco que pode ignorar diferenças de maiúsculas, o primeiro está em `case-variants/`, com o caminho original registrado no manifesto. O arquivo de Medic é uma alternativa opcional do guia; o candidato v1.5.0 permanece em diretório explicitamente incompleto.

O destino final foi inspecionado antes da criação. Nenhum trabalho anterior foi sobrescrito. Não há remoto configurado e nada foi publicado. `AuthorDate` registra o horário UTC da mensagem; `CommitDate` registra a importação. O conteúdo é preservado com suas inconsistências, sem correções funcionais ou alegação de compatibilidade com Bazzite.
''')

# Hash every final tracked file outside Git internals before the documentation commit.
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: record provenance, revisions, static validation and source gaps')
assert not git('status', '--porcelain')
assert not git('remote')
assert int(git('rev-list', '--count', 'HEAD')) == 23
git('fsck', '--full', '--strict')
summary = {'staged_repo': str(REPO), 'artifact_paths': len(paths), 'revision_records': len(all_writes),
           'classification': dict(types), 'content_commits': len(records), 'total_commits': 23,
           'sha256_revision_checks': hash_checks, 'python_static_parses': syntax_checks,
           'head': git('rev-parse', 'HEAD').strip(), 'status_porcelain': git('status', '--porcelain'),
           'remotes': git('remote', '-v'), 'tracked_files': len(git('ls-files').splitlines())}
(ROOT / 'verification-staged.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(git('log', '--reverse', '--format=%h %aI %s'))
