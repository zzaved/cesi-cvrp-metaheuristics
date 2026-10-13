import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import RouteMap from '@site/src/components/RouteMap';
import styles from './index.module.css';

/**
 * The front page states the problem in one sentence, shows it in one picture,
 * and then offers one card per folder of the documentation.
 */

const ROUTES = [
  {
    to: '/docs/intro',
    eyebrow: 'Start here',
    title: 'What this project is',
    body: 'The ADEME call, the two scope levels, and a map of how this documentation is organized.',
  },
  {
    to: '/docs/task-separation',
    eyebrow: 'Who does what',
    title: 'Task separation',
    body: 'Three lanes, Person 1, 2 and 3, each owning one part of the model, the solver or the study.',
  },
  {
    to: '/docs/discovery/problem-mapping',
    eyebrow: 'Discovery',
    title: 'Problem mapping',
    body: 'The problem statement, every constraint classified, assumptions, success criteria and risks.',
  },
  {
    to: '/docs/technical/ilp-model',
    eyebrow: 'Technical',
    title: 'Model and solver',
    body: 'Formal model, NP-hardness proof, ILP formulations and the ALNS metaheuristic.',
  },
  {
    to: '/docs/experimentation/experimental-design',
    eyebrow: 'Experimentation',
    title: 'How we prove it works',
    body: 'Twenty plus instances, seeds, gap to best known, time scaling and paired statistical tests.',
  },
  {
    to: '/docs/delivery/checklist',
    eyebrow: 'Delivery',
    title: 'What we hand in',
    body: 'Both deliverables, the presentation, the grading criteria and the checklist that tracks them.',
  },
];

export default function Home(): React.ReactElement {
  return (
    <Layout
      title="Shorter delivery routes"
      description="CVRP and CVRPTW solver for the ADEME smart mobility call: ILP model, ALNS metaheuristic, VRPLIB benchmarks and a statistical study."
    >
      <header className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroText}>
            <p className={styles.eyebrow}>CESI · Algorithms and Combinatorial Optimization</p>
            <h1 className={styles.title}>Shorter routes, fewer emissions.</h1>
            <p className={styles.lead}>
              CesiCDP answers the ADEME call on smart, low emission mobility with a delivery route
              optimizer. Every truck leaves the depot, serves a subset of customers within its
              capacity, and comes back; we look for the set of routes with the lowest total
              duration, first for the capacitated problem (CVRP) and then with delivery time
              windows (CVRPTW).
            </p>
            <div className={styles.actions}>
              <Link className={styles.primary} to="/docs/intro">
                Read the documentation
              </Link>
              <Link className={styles.secondary} to="/docs/task-separation">
                See who does what
              </Link>
            </div>
            <p className={styles.byline}>Pablo, Dag and Farida.</p>
          </div>

          <div className={styles.heroMap}>
            <RouteMap size={300} />
            <p className={styles.mapCaption}>One depot, three trucks, every customer once.</p>
          </div>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.grid}>
          {ROUTES.map((route) => (
            <Link key={route.to} to={route.to} className={styles.card}>
              <p className={styles.cardEyebrow}>{route.eyebrow}</p>
              <h2 className={styles.cardTitle}>{route.title}</h2>
              <p className={styles.cardBody}>{route.body}</p>
            </Link>
          ))}
        </div>
      </main>
    </Layout>
  );
}
