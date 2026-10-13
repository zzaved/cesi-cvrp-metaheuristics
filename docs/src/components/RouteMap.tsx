import React from 'react';
import styles from './RouteMap.module.css';

/**
 * A hand-placed CVRP solution: one depot, fourteen customers, three routes.
 * Each route draws itself in turn, which is the whole project in one picture:
 * leave the depot, visit a subset of customers, come back.
 */

type Point = [number, number];

const DEPOT: Point = [160, 160];

const ROUTES: Point[][] = [
  [[96, 70], [52, 112], [40, 176], [84, 214]],
  [[150, 46], [214, 34], [270, 80], [262, 140], [210, 120]],
  [[226, 200], [272, 238], [220, 282], [150, 276], [116, 238]],
];

function toPath(route: Point[]): string {
  const pts = [DEPOT, ...route, DEPOT];
  return pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x} ${y}`).join(' ');
}

export default function RouteMap({size = 320}: {size?: number}): React.ReactElement {
  return (
    <svg
      className={styles.map}
      width={size}
      height={size}
      viewBox="0 0 320 320"
      role="img"
      aria-label="Three delivery routes leaving a central depot and returning to it"
    >
      {ROUTES.map((route, k) => (
        <path
          key={`r${k}`}
          d={toPath(route)}
          className={styles.route}
          style={{animationDelay: `${k * 0.9}s`}}
          pathLength={1}
        />
      ))}
      {ROUTES.flat().map(([x, y], i) => (
        <circle key={`c${i}`} cx={x} cy={y} r={7} className={styles.customer} />
      ))}
      <rect x={DEPOT[0] - 12} y={DEPOT[1] - 12} width={24} height={24} rx={5} className={styles.depot} />
    </svg>
  );
}
