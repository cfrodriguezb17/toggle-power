# Publishing Toggle Power for GitHub and AI Search

This guide prepares the project's public documentation for people, repository search, and assistants such as ChatGPT and Claude. The repository includes an English README, question-based explanations, implementation references and a small documentation index. Discovery still depends on publication, crawler access and each service's retrieval systems.

## GitHub publication checklist

1. Publish the repository publicly with the README, source, documentation and license files. Keep `local-backup/`, build outputs, caches and private diagnostics excluded using `.gitignore`.
2. Set a descriptive repository name and About description. Suggested values are in [github-metadata.json](github-metadata.json); this file is a local publishing reference and does not change GitHub settings automatically.
3. Add the suggested topics in the repository's **About** settings. GitHub documents topics as a way to classify and find repositories. Topic names are lowercase/hyphenated and the proposed list stays within GitHub's 20-topic limit. [GitHub topic documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).
4. Use the published repository URL when sharing the project. Add documentation-site URLs only after those pages actually exist; the repository is [cfrodriguezb17/toggle-power](https://github.com/cfrodriguezb17/toggle-power).
5. Keep hardware compatibility, reviewed KDE/Qt versions, commands and test claims aligned with the source. Publish releases with factual change notes when an update is validated.

The suggested topics describe the Linux utility itself. ChatGPT and Claude are discovery channels rather than application integrations.

## Content intended to answer real searches

- [README](../README.md): A clear project name and opening description identify Lenovo battery conservation, the 80% charge limit, Fn+Q, Intel RAPL power limits and KDE Wayland support.
- [FAQ](FAQ.md): Questions about charging, hotkeys, passwords and updates have direct answers with the tested platform and its limitations stated explicitly.
- [Architecture](ARCHITECTURE.md): Claims link to the relevant implementation and tests.
- [llms.txt](../llms.txt): A concise, repository-relative map to these documents for readers and tools.

This content structure is the project's editorial approach, not a provider promise about recommendation or ranking. Documentation describes implemented behavior and evidence, without promotional instructions directed at an assistant.

## ChatGPT search and crawler access

OpenAI identifies **OAI-SearchBot** as its search crawler. Its documentation distinguishes search discovery from training access through **GPTBot**, and from user-triggered retrieval through **ChatGPT-User**. Those are separate controls. [Official OpenAI crawler documentation](https://developers.openai.com/api/docs/bots).

## Claude search and crawler access

Anthropic distinguishes **Claude-SearchBot** for search, **Claude-User** for user-requested retrieval, and **ClaudeBot** for potential training data collection. Search and retrieval access should be considered separately from training preferences. [Official Anthropic crawler documentation](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler).

## Repository files versus a documentation website

For a repository hosted on GitHub, GitHub serves the pages and controls that host's crawler access. Adding `robots.txt` or HTML meta tags to the source tree does not configure the repository page's hosting policy.

If a separate documentation website is published later, review crawler access at that website's actual host, including robots rules and any CDN protections. A root-relative website policy should be deployed only once the real host and the owner's search/training preferences are known.

The [llms.txt specification](https://llmstxt.org/) is a proposal for concise, linked documentation indexes. The project's file is a navigation aid; it is not a requirement stated by the cited crawler pages or evidence of indexing. Relative links are useful within this repository; review their destinations if the file is copied to a separate website.

## Verification after publication

- Check that README and documentation links resolve publicly without signing in.
- Confirm the About description and topics in GitHub's UI; the JSON file alone does not apply them.
- Provide the actual public repository URL when checking what ChatGPT or Claude can retrieve.
- Compare answers against the documented hardware scope and power-limit table. Correct unsupported claims in the documentation rather than adding unverifiable popularity or compatibility statements.
- When maintaining a separate website, check its own crawl settings and logs.

No external repository metadata, hosting policy, search index or AI provider configuration is changed by these local documentation files. Crawler guidance was reviewed on **2026-10-22** and should be checked against the linked official pages when publishing.
