import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const REPO = 'https://github.com/zzaved/cesi-cvrp-metaheuristics';

const config: Config = {
  title: 'CVRP Metaheuristics',
  tagline: 'Shorter delivery routes for the ADEME smart mobility call',
  favicon: 'img/favicon.svg',

  future: {
    v4: true,
  },

  // GitHub Pages.
  url: 'https://zzaved.github.io',
  baseUrl: '/cesi-cvrp-metaheuristics/',
  organizationName: 'zzaved',
  projectName: 'cesi-cvrp-metaheuristics',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  markdown: {
    // .md files are plain CommonMark (braces in math and prose are safe);
    // only .mdx files are parsed as MDX.
    format: 'detect',
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  themes: ['@docusaurus/theme-mermaid'],

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
      type: 'text/css',
      crossorigin: 'anonymous',
    },
  ],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          // Content lives in docs/content so the site root (docs/) can hold
          // the Docusaurus tooling without a confusing docs/docs folder.
          path: 'content',
          routeBasePath: 'docs',
          sidebarPath: './sidebars.ts',
          editUrl: `${REPO}/tree/main/docs/`,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
    navbar: {
      title: 'CVRP Metaheuristics',
      logo: {
        alt: 'CVRP Metaheuristics',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {to: '/docs/task-separation', label: 'Task separation', position: 'left'},
        {href: REPO, label: 'GitHub', position: 'right'},
      ],
    },
    footer: {
      style: 'light',
      links: [
        {
          title: 'Read',
          items: [
            {label: 'Start here', to: '/docs/intro'},
            {label: 'Problem mapping', to: '/docs/discovery/problem-mapping'},
            {label: 'ILP model', to: '/docs/technical/ilp-model'},
          ],
        },
        {
          title: 'Work',
          items: [
            {label: 'Task separation', to: '/docs/task-separation'},
            {label: 'Schedule', to: '/docs/management/schedule'},
            {label: 'Checklist', to: '/docs/delivery/checklist'},
          ],
        },
        {
          title: 'Source',
          items: [
            {label: 'GitHub', href: REPO},
            {label: 'Notebooks', href: `${REPO}/tree/main/notebooks`},
          ],
        },
      ],
      copyright:
        'CesiCDP: Pablo, Dag and Farida. CESI Ecole d\'Ingenieurs, Algorithms and Combinatorial Optimization, 2026.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
