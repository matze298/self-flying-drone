function renderMermaid() {
  if (window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: document.body.dataset.mdColorScheme === 'slate' ? 'dark' : 'default',
      flowchart: { useMaxWidth: true, htmlLabels: true }
    });
    window.mermaid.run({ querySelector: '.mermaid' });
  }
}

if (typeof document$ !== 'undefined') {
  document$.subscribe(renderMermaid);
} else {
  document.addEventListener('DOMContentLoaded', renderMermaid);
}
