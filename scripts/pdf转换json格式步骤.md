## Initiating Information Extraction&Processing PDF Content
grabbing text snippets from several pages to get a feel for the structure. Page zero is up, and I'm eyeing the layout and text flow. The goal is to identify Q&A patterns.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(f'Total pages: {len(doc)}')
for i in [0, 20, 60, 100]:
    if i < len(doc):
        print(f'--- Page {i} ---')
        print(doc[i].get_text()[:400])


## I'm digging into page 100, which offers a trove of interview questions. I'm focusing on those specific points. TIME_WAIT, TCP stick, epoll, deadlocks, and zombie processes -- all rich with potential for deeper exploration. I'm parsing this for specific questions to formulate a Q&A model.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in [10, 30, 50, 70, 90]:
    if i < len(doc):
        print(f'--- Page {i} ---')
        print(doc[i].get_text()[:400])

## Considering Recent Developments
I've been drilling down into the last PDF section. My focus is primarily on those system design scenarios, with the local cache and RPC framework challenges drawing my attention. The algorithms and brain teasers are useful, but I'm prioritizing the more complex system design aspects at this point. I've begun outlining potential architectures for both, aiming for a scalable solution in each instance.
Focusing on Extraction
I'm now prioritizing the extraction of specific topics from the PDF. I'm isolating questions related to system design, such as designing an RPC framework, and applying those. Consistent hashing is next, followed by OS-related questions about Deadlocks and Zombie processes. My aim is to convert these topics into actionable QA pairs.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
# Let's search for RPC
for i in range(len(doc)):
    text = doc[i].get_text()
    if '设计一个RPC' in text:
        print(f'--- Page {i} ---')
        print(text[:800])

## Investigating the PDF Structure
I've made some progress, and now I'm starting to see how these documents are organized. It seems like we have sections or parts. The page numbers, 90, 102, don't help. I need the content, and it looks like a collection of PDFs. Finding the original would speed things up; maybe I'll try searching for phrases like "僵尸进程" and "死锁的".
Deciphering PDF Fragments
The pieces are fitting together. I'm realizing these page ranges point to a larger document broken into segments, as hinted by the file naming conventions. It seems like I need to reconstruct this PDF somehow. Time to use some search terms like "僵尸进程" to pull the content I need from the files.


import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    text = doc[i].get_text()
    if '1 亿个数据取出最大前' in text or '设计一个RPC框架' in text or '大文件排序' in text or '僵尸进程' in text:
        print(f'--- Page {i} ---')
        print(text[:400].replace('\n', ' '))


## Scanning for content
I've located some important information, like the fact that the meaty content should be before page 90. Furthermore, I've noted a key phrase or example on a specific page that I'll need to examine closely: "1亿个数据取出最大前100."

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    text = doc[i].get_text()
    if '分库分表' in text:
        print(f'--- Page {i} ---')

## Analyzing the References
I've just started to look at pages 24-26, and I'm focusing on "分库分 表". I'm curious to see how the material explains it. I'm taking notes on the key points, looking for clarity and connections. I'll summarize after reviewing those pages.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(doc[24].get_text()[:400].replace('\n', ' '))
print(doc[26].get_text()[:400].replace('\n', ' '))

## Investigating Sharding Keys

I've been drilling down into the complexities of sharding, specifically focusing on key selection. My thinking now revolves around critical factors to weigh. I'm considering scenarios, for example data skew with seller IDs vs user IDs, as well as the frequency of queries on different fields. I must figure out the secondary index implications.

Examining Key Factors

I'm now contemplating specific scenarios for sharding key selection. Considering the implications of choosing seller IDs versus user IDs as keys has been valuable. I'm focusing on data distribution and anticipating query patterns. I am also investigating secondary index strategies to improve performance for queries unrelated to the sharding keys themselves.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    text = doc[i].get_text()
    if '1亿个数据' in text or '1 亿个数据' in text:
        print(f'--- Page {i} ---')

## Searching for Clues

I'm digging deeper into the document now. It seems I'm still on page 102. I've switched gears and am now searching for key terms within the PDF itself, specifically looking for "最大前" or "堆" to pinpoint the relevant section and see if the problem statement is written differently than I initially thought.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    text = doc[i].get_text()
    if '最大前' in text or '数据取出' in text:
        print(f'--- Page {i} ---')

## Searching for Relevant Pages

I'm now investigating search terms to pinpoint the desired information. I've tried queries related to "大文件排序" and "猴子搬香蕉," hoping to uncover related content. The initial results appear somewhat promising, and I'll continue to refine the search.


import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    text = doc[i].get_text()
    if '猴子' in text or '香蕉' in text:
        print(f'--- Page {i} ---')

## Reviewing the Material

I'm currently on page 87 and taking notes as I review the material. My initial focus is on understanding the core arguments presented in this section, and I'm identifying key points. I'm also cross-referencing with earlier chapters to build a comprehensive view of the context.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(doc[87].get_text()[:400].replace('\n', ' '))

## Analyzing the Index

I've re-examined the initial index. I noticed the content for some items like "猴子搬香蕉" is missing details. Then I checked the timestamp, and am now searching for "白鼠找毒药" as it is the next topic.

Revisiting the Timeline

I'm now going through the index again. I realized there are some missing content details for a few topics like "猴子搬香蕉". The timeline information, including the date "2025.04.19," prompted me to look into "白鼠找毒药," "金条," and "鸡蛋." I'm also cross-referencing to the specific page numbers noted, and currently reexamining the content on pages around 55, 56, and 57, after recalling the two-egg problem appearing on page 60.


import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(doc[60].get_text()[:200].replace('\n', ' '))

## Considering title precision

I'm checking the title's accuracy. I need to make sure "猴子搬香蕉" is the correct and best title for the content. Next, I'm examining pages related to "分库分表" and other surrounding concepts. It appears on pages 24-26, 28, 33, and 34. I'm also looking at other, nearby page topics.

Examining related topics

Okay, so the title's accuracy is still in question. I'm focusing on "分库分表" and nearby page topics to see if the title is right. I'm also now analyzing the topics around other pages to understand context. Page 5, 15, 35, 45, 70, and 80 are next.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in [5, 15, 35, 45, 65, 75, 85]:
    if i < len(doc):
        print(f'--- Page {i} ---')
        print(doc[i].get_text()[:300].replace('\n', ' '))

## Exploring Contingencies & Patterns

I've been focusing on the "Redis 挂了怎么办" scenario, outlining monitoring, rate limiting, and fallback mechanisms. Alongside this, I'm examining the Singleton Pattern, specifically comparing eager and lazy initialization, and emphasizing thread safety considerations. The goal is to build robust systems.

Integrating Components and Logic

I'm now integrating the "Redis 挂了怎么办" scenario, along with Singleton Pattern, sharding and consistent hashing details. I plan to construct the backend_technical and scenarios json with these elements. I am deciding how to categorize the AI/Algorithm questions; I'm leaning toward including them within scenarios or behavioral sections, perhaps. Next, I need to elaborate the QA for the "Redis 挂了怎么办" scenario.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(doc[5].get_text().replace('\n', ' '))
print(doc[6].get_text().replace('\n', ' '))

## Analyzing a Problem Scenario

I'm now formulating a question: "What to do if a project's Redis dependency fails?" I'm outlining key areas, including monitoring and discovery, rate-limiting, implementing database fallbacks, and pre-configured switches. Next, I'll explore retrieving the largest ten items from a dataset of 100 million.

Exploring Dependency Failures

I'm refining my question: "How to handle a Redis dependency failure in a project?" I'm structuring the approach with monitoring, rate-limiting, and database fallbacks. I've switched to researching the "Top-K" problem for efficiency, looking for the best approaches. I'm focusing on "Heap" and exploring "quick sort" and "merge sort" methods.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    if '取出最大前' in doc[i].get_text() and float(i)<90:
        print(f'--- Page {i} ---', doc[i].get_text().replace('\n', ' ')[:400])

## Refining Search Queries

I'm now investigating alternative phrasing for the initial query. It seems like the exact term wasn't recognized. I'm testing "最大前 100" to see if this yields better results. This is part of the ongoing refinement of the search parameters to obtain the correct data.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
for i in range(len(doc)):
    if '100' in doc[i].get_text() and '亿' in doc[i].get_text():
        print(f'--- Page {i} ---')

## Identifying the Scope

I've pinpointed the key term: "1亿个数据取出最大前 100个" (Get the top 100 from 100 million data points). My current focus is on how this concept is framed in the context of the document. The table of contents seems to list it, but it could be under a different title like "海量数据处理" (Massive Data Processing) in the body.

Re-Evaluating Strategy

Okay, it looks like I need to decide between focusing on the main topic, "Get top 100 from 100 million data," which is a classic, or branching out to "25 horses find top 3," or the other topics listed. I'll read about Consistency Hash now to see if that's a better path. I'm leaning toward the main topic, though.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(doc[29].get_text().replace('\n', ' ')[:500])
print(doc[30].get_text().replace('\n', ' ')[:500])

## Examining Sharding Strategies

I've been drilling down into the "分库分表" strategy, particularly for sharding order tables. Currently, I'm evaluating the optimal sharding key, considering both UserID and SellerID. My main concern is balancing query frequency and preventing data skew from large sellers. Further refinement is needed for non-sharding key queries.

Evaluating Query Optimization Techniques

I'm now shifting my focus to query optimization methods. Building on the sharding key analysis, I'm examining how Elasticsearch, local mapping tables, and broadcast queries can address scenarios where sharding keys aren't used. My next task will be to assess the performance implications of each approach, especially concerning data retrieval speed.

import fitz
doc = fitz.open('knowledge-base/（已压缩）backend面试知识(1)/（已压缩）backend面试知识(1)_216-426_107-211.pdf')
print(doc[65].get_text().replace('\n', ' ')[:500])
print(doc[66].get_text().replace('\n', ' ')[:500])