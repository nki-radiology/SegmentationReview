module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    // Enforce our scopes
    "scope-enum": [
      2,
      "always",
      [
        "loader",
        "exporter",
        "ui",
        "review",
        "ci",
        "deps",
        "tutorial",
        "tests",
        "release",
      ],
    ],
    "subject-case": [2, "always", "lower-case"],
    "header-max-length": [2, "always", 72],
    "body-max-line-length": [1, "always", 100],
  },
};
