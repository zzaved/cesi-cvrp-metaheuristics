---
sidebar_position: 2
title: Working agreements
---

# Working agreements

How the three of us work together. Changes to this page are agreed in a weekly meeting.

## Meeting roles

The prosit method uses four roles; with three people, the **manager** role is held by whoever is
facilitator that week. Roles rotate every week so everyone holds each one.

| Role | Does | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 |
| --- | --- | --- | --- | --- | --- | --- |
| Facilitator and manager | runs the meeting, keeps time, tracks the schedule and the checklist | Person 1 | Person 2 | Person 3 | Person 1 | Person 2 |
| Secretary | writes decisions and actions on the board | Person 2 | Person 3 | Person 1 | Person 2 | Person 3 |
| Scribe | writes the minutes into the kickoff or weekly page | Person 3 | Person 1 | Person 2 | Person 3 | Person 1 |

## Weekly self-study meeting

- **When:** once a week, slot decided at kickoff (D8). 45 minutes.
- **Agenda:** each lane in 5 minutes (done, next, blocked); checklist review; decisions; next roles.
- **Output:** minutes appended to [Schedule](./schedule.md#weekly-log).

## Git workflow

- `main` is always green (CI passes) and is never pushed to directly.
- One branch per task, named after the task ID: `p1-06-ilp-mtz`, `p2-02-swap`, `p3-01-instances`.
- Pull request into `main`, reviewed by the lane in the [review rotation](../task-separation.md#the-three-lanes-at-a-glance)
  (Person 1 reviews Person 2, Person 2 reviews Person 3, Person 3 reviews Person 1).
- Commit messages in English, conventional style: `feat(alns): add regret-2 insertion`,
  `docs(ilp): time window constraints`, `test: relocate keeps capacity`.
- Notebooks: clear outputs before committing, except the final versions handed in.

## Definition of done

A task is done when:

1. the code has docstrings, type hints and passes `make lint` and `make test`;
2. it has at least one test (or, for documentation, a reviewer read it);
3. the related documentation page and `TODO` markers are updated;
4. the pull request is merged into `main`.

## Writing conventions

- Everything in the repository is in **English**.
- No em dashes or en dashes as punctuation: use colons, commas, semicolons or parentheses.
- Unverified facts are marked *to verify*; hypotheses are never written as results.
