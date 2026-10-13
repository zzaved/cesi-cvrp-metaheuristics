import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * Two entry documents, then six folders that answer six different questions.
 * Nothing belongs in two places and nothing is left over:
 *
 *   Discovery        why, and what exactly is the problem
 *   Technical        how we model and solve it
 *   Experimentation  how we prove the solver is good
 *   Delivery         what we hand in, and how it is graded
 *   Management       how the three of us work, and when
 *   Reference        words and sources to look up
 */
const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    'task-separation',
    {
      type: 'category',
      label: 'Discovery',
      collapsed: false,
      items: ['discovery/context', 'discovery/exploration-sheet', 'discovery/problem-mapping'],
    },
    {
      type: 'category',
      label: 'Technical',
      collapsed: false,
      items: [
        'technical/modeling',
        'technical/complexity',
        'technical/ilp-model',
        'technical/metaheuristic',
        'technical/architecture',
      ],
    },
    {
      type: 'category',
      label: 'Experimentation',
      collapsed: true,
      items: [
        'experimentation/instances',
        'experimentation/experimental-design',
        'experimentation/results',
      ],
    },
    {
      type: 'category',
      label: 'Delivery',
      collapsed: true,
      items: ['delivery/deliverables', 'delivery/checklist', 'delivery/presentation-plan'],
    },
    {
      type: 'category',
      label: 'Management',
      collapsed: true,
      items: ['management/kickoff-meeting', 'management/working-agreements', 'management/schedule'],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: true,
      items: ['reference/glossary', 'reference/bibliography'],
    },
  ],
};

export default sidebars;
