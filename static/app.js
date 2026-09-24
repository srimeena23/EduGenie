document.addEventListener("DOMContentLoaded", () => {
    const askForm = document.getElementById("askForm");
    const explainForm = document.getElementById("explainForm");
    const summarizeForm = document.getElementById("summarizeForm");
    const quizForm = document.getElementById("quizForm");
    const learningPathForm = document.getElementById("learningPathForm");

    const askResult = document.getElementById("askResult");
    const explainResult = document.getElementById("explainResult");
    const summarizeResult = document.getElementById("summarizeResult");
    const quizResult = document.getElementById("quizResult");
    const learningPathResult = document.getElementById("learningPathResult");


    // ---------------------------------------------------------
    // HELPER FUNCTION
    // ---------------------------------------------------------

    async function sendRequest(url, data) {

        const response = await fetch(url, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Something went wrong."
            );
        }

        return result;
    }


    // ---------------------------------------------------------
    // DISPLAY ERROR
    // ---------------------------------------------------------

    function showError(element, error) {

        element.innerHTML = `
            <div class="error-message">
                ${escapeHtml(error.message)}
            </div>
        `;
    }


    // ---------------------------------------------------------
    // ESCAPE HTML
    // ---------------------------------------------------------

    function escapeHtml(value) {

        const div = document.createElement("div");

        div.textContent = value;

        return div.innerHTML;
    }


    // ---------------------------------------------------------
    // ASK EDU GENIE
    // ---------------------------------------------------------

    if (askForm) {

        askForm.addEventListener("submit", async (event) => {

            event.preventDefault();

            const question =
                document.getElementById("question").value.trim();

            if (!question) {
                askResult.innerHTML =
                    `<div class="error-message">
                        Please enter a question.
                    </div>`;

                return;
            }

            askResult.innerHTML =
                `<div class="loading">Thinking...</div>`;

            try {

                const result = await sendRequest(
                    "/api/ask",
                    {
                        question: question
                    }
                );

                askResult.innerHTML = `
                    <div class="result-card">
                        <h3>Answer</h3>
                        <div class="result-text">
                            ${formatText(result.answer)}
                        </div>
                    </div>
                `;

            } catch (error) {

                showError(
                    askResult,
                    error
                );
            }
        });
    }


    // ---------------------------------------------------------
    // EXPLAIN SIMPLY
    // ---------------------------------------------------------

    if (explainForm) {

        explainForm.addEventListener("submit", async (event) => {

            event.preventDefault();

            const text =
                document.getElementById("explainText").value.trim();

            if (!text) {

                explainResult.innerHTML =
                    `<div class="error-message">
                        Please enter a concept.
                    </div>`;

                return;
            }

            explainResult.innerHTML =
                `<div class="loading">Preparing a simple explanation...</div>`;

            try {

                const result = await sendRequest(
                    "/api/explain",
                    {
                        text: text
                    }
                );

                explainResult.innerHTML = `
                    <div class="result-card">
                        <h3>Simple Explanation</h3>
                        <div class="result-text">
                            ${formatText(result.answer)}
                        </div>
                    </div>
                `;

            } catch (error) {

                showError(
                    explainResult,
                    error
                );
            }
        });
    }


    // ---------------------------------------------------------
    // SUMMARIZE
    // ---------------------------------------------------------

    if (summarizeForm) {

        summarizeForm.addEventListener("submit", async (event) => {

            event.preventDefault();

            const text =
                document.getElementById("summaryText").value.trim();

            if (!text) {

                summarizeResult.innerHTML =
                    `<div class="error-message">
                        Please enter some text to summarize.
                    </div>`;

                return;
            }

            summarizeResult.innerHTML =
                `<div class="loading">Creating summary...</div>`;

            try {

                const result = await sendRequest(
                    "/api/summarize",
                    {
                        text: text
                    }
                );

                summarizeResult.innerHTML = `
                    <div class="result-card">
                        <h3>Summary</h3>
                        <div class="result-text">
                            ${formatText(result.answer)}
                        </div>
                    </div>
                `;

            } catch (error) {

                showError(
                    summarizeResult,
                    error
                );
            }
        });
    }


    // ---------------------------------------------------------
    // GENERATE QUIZ
    // ---------------------------------------------------------

    if (quizForm) {

        quizForm.addEventListener("submit", async (event) => {

            event.preventDefault();

            const topic =
                document.getElementById("quizTopic").value.trim();

            const numberOfQuestions =
                Number(
                    document.getElementById(
                        "numberOfQuestions"
                    ).value
                );

            if (!topic) {

                quizResult.innerHTML =
                    `<div class="error-message">
                        Please enter a quiz topic.
                    </div>`;

                return;
            }

            quizResult.innerHTML =
                `<div class="loading">Generating quiz...</div>`;

            try {

                const result = await sendRequest(
                    "/api/quiz",
                    {
                        topic: topic,
                        number_of_questions:
                            numberOfQuestions
                    }
                );

                displayQuiz(result);

            } catch (error) {

                showError(
                    quizResult,
                    error
                );
            }
        });
    }


    // ---------------------------------------------------------
    // DISPLAY QUIZ
    // ---------------------------------------------------------

    function displayQuiz(quiz) {

        let html = `
            <div class="result-card">
                <h3>${escapeHtml(quiz.title)}</h3>
        `;

        quiz.questions.forEach((question, index) => {

            html += `
                <div class="quiz-question">

                    <h4>
                        ${index + 1}. 
                        ${escapeHtml(question.question)}
                    </h4>

                    <div class="quiz-options">
            `;

            question.options.forEach((option) => {

                html += `
                    <div class="quiz-option">
                        ${escapeHtml(option)}
                    </div>
                `;
            });

            html += `
                    </div>

                    <div class="quiz-answer">
                        <strong>Answer:</strong>
                        ${escapeHtml(question.answer)}
                    </div>

                    <div class="quiz-explanation">
                        <strong>Explanation:</strong>
                        ${escapeHtml(question.explanation)}
                    </div>

                </div>
            `;
        });

        html += `
            </div>
        `;

        quizResult.innerHTML = html;
    }


    // ---------------------------------------------------------
    // LEARNING PATH
    // ---------------------------------------------------------

    if (learningPathForm) {

        learningPathForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();

                const topic =
                    document.getElementById(
                        "learningTopic"
                    ).value.trim();

                const level =
                    document.getElementById(
                        "learningLevel"
                    ).value;

                const weeks =
                    Number(
                        document.getElementById(
                            "learningWeeks"
                        ).value
                    );

                if (!topic) {

                    learningPathResult.innerHTML =
                        `<div class="error-message">
                            Please enter a learning topic.
                        </div>`;

                    return;
                }

                learningPathResult.innerHTML =
                    `<div class="loading">
                        Building your learning path...
                    </div>`;

                try {

                    const result = await sendRequest(
                        "/api/learning-path",
                        {
                            topic: topic,
                            level: level,
                            weeks: weeks
                        }
                    );

                    displayLearningPath(result);

                } catch (error) {

                    showError(
                        learningPathResult,
                        error
                    );
                }
            }
        );
    }


    // ---------------------------------------------------------
    // DISPLAY LEARNING PATH
    // ---------------------------------------------------------

    function displayLearningPath(path) {

        let html = `
            <div class="result-card">

                <h3>
                    ${escapeHtml(path.title)}
                </h3>

                <p>
                    ${escapeHtml(path.overview)}
                </p>

                <div class="learning-weeks">
        `;

        path.weeks.forEach((week) => {

            html += `
                <div class="week-card">

                    <h4>
                        Week ${week.week}:
                        ${escapeHtml(week.title)}
                    </h4>

                    <div class="week-section">

                        <strong>Topics</strong>

                        <ul>
            `;

            week.topics.forEach((topic) => {

                html += `
                    <li>
                        ${escapeHtml(topic)}
                    </li>
                `;
            });

            html += `
                        </ul>

                    </div>

                    <div class="week-section">

                        <strong>Practice</strong>

                        <ul>
            `;

            week.practice.forEach((practice) => {

                html += `
                    <li>
                        ${escapeHtml(practice)}
                    </li>
                `;
            });

            html += `
                        </ul>

                    </div>

                    <div class="week-goal">

                        <strong>Goal:</strong>

                        ${escapeHtml(week.goal)}

                    </div>

                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        learningPathResult.innerHTML = html;
    }


    // ---------------------------------------------------------
    // FORMAT TEXT
    // ---------------------------------------------------------

    function formatText(text) {

        let safeText =
            escapeHtml(text);

        safeText =
            safeText.replace(
                /\*\*(.*?)\*\*/g,
                "<strong>$1</strong>"
            );

        safeText =
            safeText.replace(
                /\n/g,
                "<br>"
            );

        return safeText;
    }
});