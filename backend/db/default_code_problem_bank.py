from copy import deepcopy

from db.code_problem_bank import get_hot100_problems, problem, tc


def _select_existing_problem(title: str) -> dict:
    for item in get_hot100_problems():
        if item["title"] == title:
            return deepcopy(item)
    raise KeyError(f"Problem not found: {title}")


DEFAULT_CODE_PROBLEMS = [
    _select_existing_problem("两数配对"),
    _select_existing_problem("逆序数字相加"),
    _select_existing_problem("最长无重复片段"),
    _select_existing_problem("合并有序序列"),
    _select_existing_problem("括号序列校验"),
    _select_existing_problem("二叉树层序遍历"),
    problem(
        101,
        "岛屿数量",
        "number-of-islands-acm",
        "中等",
        ["图", "DFS", "BFS"],
        "给定一个由字符 `0` 和 `1` 组成的二维网格，`1` 表示陆地，`0` 表示海水。上下左右相连的陆地视为同一座岛屿。请输出岛屿数量。",
        "第一行输入两个整数 m 和 n。接下来输入 m 行，每行是一个长度为 n 的仅包含 `0` 和 `1` 的字符串。",
        "输出一个整数，表示岛屿数量。",
        [
            {
                "input": "4 5\n11000\n11000\n00100\n00011\n",
                "output": "3",
                "explanation": "共有三块互不相连的陆地。",
            }
        ],
        ["1 <= m, n <= 200"],
        [
            tc("3 3\n111\n010\n111\n", "1"),
            tc("3 4\n0000\n0000\n0000\n", "0"),
            tc("1 6\n101011\n", "4"),
            tc("5 5\n10001\n00100\n00100\n10001\n11111\n", "4"),
        ],
    ),
    problem(
        102,
        "最长递增子序列",
        "longest-increasing-subsequence-acm",
        "中等",
        ["动态规划", "二分"],
        "给定一个整数序列，求其中最长严格递增子序列的长度。",
        "第一行输入整数 n。第二行输入 n 个整数。",
        "输出一个整数，表示最长严格递增子序列长度。",
        [
            {
                "input": "8\n10 9 2 5 3 7 101 18\n",
                "output": "4",
                "explanation": "最长递增子序列可以是 2 3 7 101。",
            }
        ],
        ["1 <= n <= 200000", "-10^9 <= nums[i] <= 10^9"],
        [
            tc("6\n0 1 0 3 2 3\n", "4"),
            tc("7\n7 7 7 7 7 7 7\n", "1"),
            tc("5\n5 4 3 2 1\n", "1"),
            tc("10\n1 3 6 7 9 4 10 5 6 7\n", "6"),
        ],
    ),
    problem(
        103,
        "最小覆盖子串",
        "minimum-window-substring-acm",
        "困难",
        ["字符串", "滑动窗口", "哈希表"],
        "给定字符串 s 和 t，请在 s 中找出一个最短子串，使其包含 t 中所有字符及其出现次数。若不存在则输出 -1；若有多个最短答案，输出最左侧的那个。",
        "第一行输入字符串 s。第二行输入字符串 t。",
        "输出满足条件的最短子串；若不存在则输出 -1。",
        [
            {
                "input": "ADOBECODEBANC\nABC\n",
                "output": "BANC",
                "explanation": "BANC 是最短且最左侧的覆盖子串。",
            }
        ],
        ["1 <= |s| <= 200000", "1 <= |t| <= 200000", "字符串默认区分大小写"],
        [
            tc("a\na\n", "a"),
            tc("a\naa\n", "-1"),
            tc("aa\nAA\n", "-1"),
            tc("abbbbbcdd\nabcdd\n", "abbbbbcdd"),
            tc("bdab\na\n", "a"),
        ],
    ),
    problem(
        104,
        "LRU 缓存模拟",
        "lru-cache-simulation-acm",
        "中等",
        ["设计", "哈希表", "双向链表"],
        "请实现一个容量固定的 LRU 缓存。支持两种操作：`put key value` 表示写入或更新；`get key` 表示读取。若命中则输出值，否则输出 -1。每次访问或写入都会让该 key 成为最近使用。",
        "第一行输入两个整数 capacity 和 q，表示缓存容量和操作数。接下来 q 行，每行是一条操作，格式为 `put key value` 或 `get key`。",
        "对每条 `get` 操作输出一行结果。",
        [
            {
                "input": "2 9\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2\nput 4 4\nget 1\nget 3\nget 4\n",
                "output": "1\n-1\n-1\n3\n4",
                "explanation": "与经典 LRU 示例一致。",
            }
        ],
        ["1 <= capacity <= 3000", "1 <= q <= 200000", "-10^9 <= key, value <= 10^9"],
        [
            tc("1 5\nput 1 10\nget 1\nput 2 20\nget 1\nget 2\n", "10\n-1\n20"),
            tc("2 6\nput 2 6\nput 1 5\nput 1 2\nget 1\nget 2\nget 3\n", "2\n6\n-1"),
            tc("3 8\nget 8\nput 8 80\nput 9 90\nput 10 100\nget 8\nput 11 110\nget 9\nget 10\n", "-1\n80\n-1\n100"),
        ],
    ),
]


def get_default_code_problems() -> list[dict]:
    return deepcopy(DEFAULT_CODE_PROBLEMS)
