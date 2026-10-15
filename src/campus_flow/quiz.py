"""Engineering Understanding Check (Engineer B: feat/22-search-and-insights).

A short multiple-choice quiz that verifies a reviewer understands the rules
CampusFlow actually enforces. Grading is strict: a choice outside A-D is
rejected as invalid rather than being counted as a wrong answer.
"""

VALID_CHOICES = ("A", "B", "C", "D")


class EngineeringQuiz:
    """Static question bank plus a strict grader."""

    # The six questions the review asks for, each about a rule the code
    # actually enforces: the unassigned guard, the empty-dataset report, strict
    # AND filtering, the resolved lock on notes, duplicate IDs at load time, and
    # why a pull request with no negative test is not evidence.
    #
    # Each question places its correct option at the letter recorded in
    # "answer", and tests/test_quiz.py derives that letter independently: it
    # exercises the rule the question is about, then locates the matching option
    # by its wording rather than by its position. Reordering a question's options
    # is therefore safe as long as "answer" is updated to whichever option still
    # describes the enforced rule. A key that disagrees with the code fails the
    # suite instead of passing it -- which is what happened before D8 was fixed
    # (see baseline-check.md).
    QUESTIONS = {
        1: {
            "question": (
                "An open ticket has no assignee. What does update_workflow() do "
                "when it is asked to move that ticket to in_progress?"
            ),
            "options": {
                "A": "Moves it to in_progress and leaves it unassigned",
                "B": "Refuses the change: a ticket must be assigned before work can start",
                "C": "Skips in_progress and resolves the ticket instead",
                "D": "Raises KeyError because the assignee is missing",
            },
            "answer": "B",
        },
        2: {
            "question": "The dataset holds no tickets at all. What does resolution_percentage() return?",
            "options": {
                "A": "It raises ZeroDivisionError",
                "B": "100.0",
                "C": "0.0",
                "D": "None",
            },
            "answer": "C",
        },
        3: {
            "question": (
                "A search supplies a title query the ticket matches and a category "
                "filter the ticket fails. What does the search return?"
            ),
            "options": {
                "A": "The ticket, because the title query matched",
                "B": "Nothing: every supplied filter must match, so they combine with AND",
                "C": "The ticket, because filters are combined with OR",
                "D": "A ValueError, because the two filters conflict",
            },
            "answer": "B",
        },
        4: {
            "question": "A ticket is already 'resolved'. What happens when add_note() is called on it?",
            "options": {
                "A": "The note is appended as normal",
                "B": "The call is refused: a resolved ticket cannot accept new notes",
                "C": "The note is appended and the ticket is reopened automatically",
                "D": "The ticket is deleted along with its notes",
            },
            "answer": "B",
        },
        5: {
            "question": "A tickets.json file contains two records whose id is both 'T001'. What does load_tickets() do?",
            "options": {
                "A": "Loads both records and lets the duplicate resolve at lookup time",
                "B": "Rejects the whole file, so the manager starts empty rather than exposing duplicates",
                "C": "Keeps the first record and silently drops the second",
                "D": "Renumbers the second record to T002",
            },
            "answer": "B",
        },
        6: {
            "question": "A pull request adds a feature but no test that exercises a failing case. Why is that a problem?",
            "options": {
                "A": "It is not a problem: a passing test suite is what matters",
                "B": "Because extra tests slow the suite down",
                "C": "Because a suite that only covers the happy path cannot fail, so it cannot show the feature is correct",
                "D": "Because reviewers prefer larger pull requests",
            },
            "answer": "C",
        },
    }

    @classmethod
    def is_valid_choice(cls, choice):
        """True when the answer is one of A-D after trimming and upper-casing."""
        return isinstance(choice, str) and choice.strip().upper() in VALID_CHOICES

    @classmethod
    def grade_quiz(cls, answers):
        """Grade a mapping of question number to chosen letter.

        Returns ``(score, results)``. ``score`` counts only correct answers.
        Each result records the question, the normalized choice, whether that
        choice was a legal option, and whether it was correct.
        """
        if not isinstance(answers, dict):
            raise TypeError("answers must be a dict of {question_number: choice}")

        score = 0
        results = []

        for number in sorted(cls.QUESTIONS):
            correct_answer = cls.QUESTIONS[number]["answer"]
            raw_choice = answers.get(number)
            valid = cls.is_valid_choice(raw_choice)
            choice = raw_choice.strip().upper() if valid else None
            is_correct = valid and choice == correct_answer

            if is_correct:
                score += 1

            results.append(
                {
                    "question": number,
                    "choice": choice,
                    "valid_choice": valid,
                    "correct": is_correct,
                    "expected": correct_answer,
                }
            )

        return score, results

    @classmethod
    def total_questions(cls):
        return len(cls.QUESTIONS)
