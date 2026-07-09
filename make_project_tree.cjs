const fs = require("fs");
const path = require("path");

const root = process.cwd();
const maxDepth = 4;

const ignore = [
  /^\.git$/i,
  /^\.venv$/i,
  /^node_modules$/i,
  /^__pycache__$/i,
  /^\.pytest_cache$/i,
  /^\.mypy_cache$/i,
  /^\.ruff_cache$/i,
  /^\.tox$/i,
  /^\.nox$/i,
  /^dist$/i,
  /^coverage$/i,
  /^htmlcov$/i,
  /^allure-results$/i,
  /^build$/i,
  /^tmp$/i,
  /^\.tmp$/i,
  /\.pyc$/i,
  /\.pyo$/i,
  /\.log$/i,
  /\.sqlite$/i,
  /\.db$/i,
  /\.tar$/i,
  /^\.env$/i
];

function shouldIgnore(name) {
  return ignore.some((rule) => rule.test(name));
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function walk(dir, prefix = "", depth = 0) {
  if (depth >= maxDepth) return [];

  let entries = fs.readdirSync(dir, { withFileTypes: true })
    .filter((entry) => !shouldIgnore(entry.name))
    .sort((a, b) => {
      if (a.isDirectory() !== b.isDirectory()) return a.isDirectory() ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

  const lines = [];

  entries.forEach((entry, index) => {
    const fullPath = path.join(dir, entry.name);
    const isLast = index === entries.length - 1;
    const branch = isLast ? "`-- " : "|-- ";
    const nextPrefix = prefix + (isLast ? "    " : "|   ");

    if (entry.isDirectory()) {
      lines.push(`${prefix}${branch}${entry.name}/`);
      lines.push(...walk(fullPath, nextPrefix, depth + 1));
    } else {
      const stat = fs.statSync(fullPath);
      lines.push(`${prefix}${branch}${entry.name} (${formatSize(stat.size)})`);
    }
  });

  return lines;
}

const output = [
  "./",
  ...walk(root)
].join("\r\n");

fs.writeFileSync("project_tree.txt", "\uFEFF" + output, "utf8");

console.log("OK: project_tree.txt generated");
