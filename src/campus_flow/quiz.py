"""Engineering Understanding Check (Engineer B: feat/22-search-and-insights).

A short multiple-choice quiz that verifies a reviewer understands the rules
CampusFlow actually enforces. Grading is strict: a choice outside A-D is
rejected as invalid rather than being counted as a wrong answer.
"""

VALID_CHOICES = ("A", "B", "C", "D")


class EngineeringQuiz:
    """Static question bank plus a strict grader."""

    # The grading fixture in tests/test_campusflow_next.py fixes the expected
    # answer letters at B, C, B, C, C, B, so each question below places its
    # correct option at that letter. The questions describe rules this
    # codebase genuinely enforces, but the letters come from the contract
    # fixture rather than from the questions themselves. If the fixture
    # changes, the options must be reordered to match.
    QUESTIONS = {
        1: {
            "question": "A ticket is open and unassigned. Which status may it move into?",
            "options": {
                "A": "resolved",
                "B": "in_progress",
                "C": "open",
                "D": "any status",
            },
            "answer": "B",
        },
        2: {
            "question": "Urgency is 'high' and affected_users is 5. What priority results?",
            "options": {
                "A": "critical",
                "B": "medium",
                "C": "high",
                "D": "low",
            },
            "answer": "C",
        },
        3: {
            "question": "How is a resolved ticket modified before further work?",
            "options": {
                "A": "It can be reassigned freely",
                "B": "It must be explicitly reopened",
                "C": "Notes may still be appended to it",
                "D": "It is archived and deleted",
            },
            "answer": "B",
        },
        4: {
            "question": "Python's bool is a subclass of int. How is True handled as affected_users?",
            "options": {
                "A": "Accepted as 1 user",
                "B": "Accepted as 0 users",
                "C": "Rejected as a boolean",
                "D": "Converted to the string 'True'",
            },
            "answer": "C",
        },
        5: {
            "question": "What is the minimum accepted length of a note message?",
            "options": {
                "A": "1 character",
                "B": "3 characters",
                "C": "5 characters",
                "D": "10 characters",
            },
            "answer": "C",
        },
        6: {
            "question": "How does save_tickets() reduce the risk of corrupting stored data?",
            "options": {
                "A": "It appends to the existing file",
                "B": "It writes a temp file, then os.replace() swaps it in",
                "C": "It keeps all state in memory only",
                "D": "It writes a second JSON backup file",
            },
            "answer": "B",
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
