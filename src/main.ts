import './styles.css';

// The courtyard is the public entrance; keep the previous portfolio accessible.
if (new URLSearchParams(window.location.search).get('tour') === 'reference') {
  await import('./portfolio/startPortfolio');
} else {
  await import('./tour/startTourPrototype');
}
