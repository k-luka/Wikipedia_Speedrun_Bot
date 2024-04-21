import wikipediaapi
import re
from collections import Counter, deque
import heapq
import wordfreq
import math

class WikiApi:
    class WikiPage:
        def __init__(self, parent_api, page_title):
            self.title = page_title
            #print(self.title)
            self.parent_wiki_api = parent_api
            self.parent = ""
            self.word_frequency = {}

        def set_parent(self, parent_wiki_page):
            self.parent = parent_wiki_page

        def get_page_links(self, page_title):
            # Fetch the page for the given title
            page = self.parent_wiki_api.wiki.page(page_title)

            # Check if the page exists
            if not page.exists():
                return "Page not found"

            # List to store titles of linked pages
            links_titles = []

            # Loop through the links on the page
            for link in page.links.values():
                # Append the title of each linked page to the list
                links_titles.append(link.title)

            return links_titles

        def get_wikipedia_page_text(self):
            # Fetch the page for the given title
            page = self.parent_wiki_api.wiki.page(self.title)

            # Check if the page exists
            if page.exists():
                # Return the text of the page
                return page.text
            else:
                return "Page not found"

        def get_word_frequency(self):
            # Check if the page was found
            text = self.get_wikipedia_page_text()
            if text == "Page not found":
                return "Page not found"

            # Clean and split the text into words, lowercasing to standardize
            words = re.findall(r'\w+', text.upper())

            # Create a Counter to count occurrences of each word, excluding stop words
            word_counts = Counter(word for word in words if word not in self.parent_wiki_api.stop_words)

            # Return sorted dictionary of words by decreasing frequency
            self.word_frequency = dict(sorted(word_counts.items(), key=lambda item: item[1], reverse=True))
            return self.word_frequency

    def __init__(self, src, tgt, word_uniqueness = True, neighbors_checked = 5):
        # Initialize the Wikipedia API
        self.wiki = wikipediaapi.Wikipedia('DSA_Project3', 'en')
        # List of common stop words to exclude
        self.stop_words = {'WAS', 'MUCH', 'WERE', 'AN', 'S', 'WHEN', 'HAD', 'BUT',
                           'IT', 'IS', 'A', 'ON', 'WHAT', 'CAN', 'HAVE', 'SHALL', 'OUT',
                           'THAN', 'BE', 'WITH', 'OF', 'DO', 'MAY', 'DOES', 'OUGHT', 'FOR',
                           'IN', 'MIGHT', 'WHO', 'WILL', 'THIS', 'ITS', 'WHICH', 'DOWN', 'BEING',
                           'MANY', 'WOULD', 'FROM', 'ABOUT', 'AS', 'COULD', 'BEEN', 'THAT',
                           'MUST', 'OR', 'SUCH', 'UP', 'HAS', 'BY', 'AND', 'DID', 'TO', 'THE',
                           'SHOULD', 'ARE', 'ALSO', 'AT'}
        self.adjust_for_word_uniqueness = word_uniqueness
        self.neighbors_to_check = neighbors_checked
        self.source_page_obj = WikiApi.WikiPage(self, src)
        self.target_page_obj = WikiApi.WikiPage(self, tgt)
        self.target_page_obj.get_word_frequency()
        self.adjacency_list = {}
        self.set_of_all_visited_sites = set()

    def set_source_page(self, src):
        del self.source_page_obj
        self.source_page_obj = WikiApi.WikiPage(self, src)

    def set_target_page(self, src):
        del self.target_page_obj
        self.target_page_obj = WikiApi.WikiPage(self, src)

    def reverse_adjust_for_word_uniqueness(self):
        self.adjust_for_word_uniqueness = not self.adjust_for_word_uniqueness

    def set_neighbors_to_check(self, n):
        self.neighbors_to_check = int(n)

    def get_adjust_for_word_uniqueness(self):
        return self.adjust_for_word_uniqueness

    def get_neighbors_to_check(self):
        return self.neighbors_to_check

    def get_adjacency_list(self):
        return self.adjacency_list

    def get_names_of_all_visited_sites(self):
        return [page.title for page in self.set_of_all_visited_sites]

    def get_number_of_visited_sites(self):
        return len(self.set_of_all_visited_sites)

    def get_length_of_path(self):
        path = self.trace_path_backwards()
        if path is not None: return len(self.trace_path_backwards()) - 1
        return 0

    def get_object_matching_page_title(self, page_title):
        for page_obj in self.set_of_all_visited_sites:
            if page_obj.title == page_title: return page_obj
        return None

    def get_most_similar_links_to_target(self, current_page):
        # List to store titles that contain any word found in the target page's word frequency list
        links_and_indices = {}
        current_links = self.target_page_obj.get_page_links(current_page)
        target_words = self.target_page_obj.word_frequency

        # Anonymous function
        split = lambda title: [word for word in title.split() if word not in self.stop_words]

        # Retrieves linked titles from the current page and splits each title into words
        title_words = {title: split(title.upper()) for title in current_links}
        # Iterates over each title and its words
        for title, words in title_words.items():
            # Check if any word in the title is in the target page's frequency dictionary
            totalFreq = 0
            for word in words:
                if word in target_words.keys():
                    # Add word times its uniqueness weight
                    word_uniqueness = wordfreq.word_frequency(word, "en")
                    if word_uniqueness <= 0: word_uniqueness_weight = lambda word: 10
                    else: word_uniqueness_weight = lambda word: -1 * math.log10(word_uniqueness) - 1
                    if not self.adjust_for_word_uniqueness: word_uniqueness_weight = lambda word: 1
                    totalFreq += target_words[word] * word_uniqueness_weight(word)
            try:
                totalFreq /= len(words)
            except:
                totalFreq = 0
            links_and_indices[title] = totalFreq

        links_and_indices = dict(sorted(links_and_indices.items(), key=lambda item: item[1], reverse=True))
        return {x: links_and_indices[x] for x in list(links_and_indices)[:self.neighbors_to_check]}

    def trace_path_backwards(self):
        if self.target_page_obj not in self.set_of_all_visited_sites: return None
        current_page_obj = self.target_page_obj
        path = []
        while current_page_obj.parent != self.source_page_obj.title:
            path.append(current_page_obj.title)
            current_page_obj = self.get_object_matching_page_title(current_page_obj.parent)
        path.append(current_page_obj.title)
        path.append(self.source_page_obj.title)
        path.reverse()
        return path

    def print_summary(self):
        print("Adjacency list: ", end="")
        print(wikiInstance.get_adjacency_list())
        print("Visited sites: ", end="")
        print(wikiInstance.get_names_of_all_visited_sites())
        print("Ordered Path: ", end="")
        if wikiInstance.trace_path_backwards() is None: print("None")
        else: print(" --> ".join(wikiInstance.trace_path_backwards()))
        print("Path length = " + str(wikiInstance.get_length_of_path()) + ", Number of visited sites = "
              + str(wikiInstance.get_number_of_visited_sites()))

    def bfs_search(self):
        queue = deque([(self.source_page_obj.title, "")])  # Queue to manage the frontier pages
        self.adjacency_list.clear()
        self.set_of_all_visited_sites.clear()

        while queue:
            current_page, current_page_parent = queue.popleft()

            # Skip revisiting pages
            if (current_page_parent != "" and self.get_object_matching_page_title(current_page)
                    in self.set_of_all_visited_sites):
                continue
            current_page_obj = WikiApi.WikiPage(self, current_page)
            current_page_obj.set_parent(current_page_parent)
            self.set_of_all_visited_sites.add(current_page_obj)

            if current_page_parent != "":
                self.adjacency_list[current_page_parent].append(current_page)
            if current_page not in self.adjacency_list.keys():
                self.adjacency_list[current_page] = []

            # Get the top 'n' similar linked pages from the current page
            try:
                related_links = self.get_most_similar_links_to_target(current_page)
                # Check if the current page is the target page
                print(str(current_page) + " links to " + str(related_links))
                if self.target_page_obj.title.upper() in [word.upper() for word in related_links.keys()]:
                    # Add target object to adjacency list and set
                    self.target_page_obj.set_parent(current_page)
                    self.set_of_all_visited_sites.add(self.target_page_obj)
                    self.adjacency_list[current_page].append(self.target_page_obj.title)
                    self.adjacency_list[self.target_page_obj.title] = []
                    return f"Target page '{self.target_page_obj.title}' found starting from '{self.source_page_obj.title}'"

            except Exception as e:
                print(f"Failed to retrieve or process links for {current_page}: {e}")
                continue

            # Enqueue unvisited linked pages
            for page in related_links.keys():
                if self.get_object_matching_page_title(page) not in self.set_of_all_visited_sites:
                    queue.append((page, current_page))

        return "Target page not found within the connected pages."

    def greedy_search(self):
        # Max heap representing our nodes to visit. Similarity indices will be inserted as
        # negative values so the min heap returns the values with actually the most similarity
        priorityQueue = []
        heapq.heappush(priorityQueue, (0, (self.source_page_obj.title, "")))
        self.adjacency_list.clear()
        self.set_of_all_visited_sites.clear()

        while priorityQueue:
            current_page, current_page_parent = heapq.heappop(priorityQueue)[1]

            # Skip revisiting pages
            if (current_page_parent != "" and self.get_object_matching_page_title(current_page)
                    in self.set_of_all_visited_sites):
                continue
            current_page_obj = WikiApi.WikiPage(self, current_page)
            current_page_obj.set_parent(current_page_parent)
            self.set_of_all_visited_sites.add(current_page_obj)

            if current_page_parent != "":
                self.adjacency_list[current_page_parent].append(current_page)
            if current_page not in self.adjacency_list.keys():
                self.adjacency_list[current_page] = []

            # Get the top 'n' similar linked pages from the current page
            try:
                related_links = self.get_most_similar_links_to_target(current_page)
                # Check if the current page is the target page
                print(str(current_page) + " links to " + str(related_links))
                if self.target_page_obj.title.upper() in [word.upper() for word in related_links.keys()]:
                    # Add target object to adjacency list and set
                    self.target_page_obj.set_parent(current_page)
                    self.set_of_all_visited_sites.add(self.target_page_obj)
                    self.adjacency_list[current_page].append(self.target_page_obj.title)
                    self.adjacency_list[self.target_page_obj.title] = []
                    return f"Target page '{self.target_page_obj.title}' found starting from '{self.source_page_obj.title}'"

            except Exception as e:
                print(f"Failed to retrieve or process links for {current_page}: {e}")
                continue

            # Enqueue unvisited linked pages
            for page, similarity_index in related_links.items():
                if self.get_object_matching_page_title(page) not in self.set_of_all_visited_sites:
                    heapq.heappush(priorityQueue, (-1 * similarity_index, (page, current_page)))

        return "Target page not found within the connected pages."

wikiInstance = WikiApi("Data structure", "Alligator")
# Yields path of length 6 in a few minutes
print(wikiInstance.bfs_search())
wikiInstance.print_summary()
print("-------------------------")
# Yields path of length 10 in a few seconds
print(wikiInstance.greedy_search())
wikiInstance.print_summary()