import numpy as np

class BoxesConnector(object):
    def __init__(self, rects, texts, imageW, max_dist=5, overlap_threshold=0.2):
        self.rects = np.array(rects)
        self.imageW = imageW
        self.texts = texts
        self.max_dist = max_dist
        self.overlap_threshold = overlap_threshold
        self.graph = np.zeros((self.rects.shape[0], self.rects.shape[0]))

        self.r_index = [[] for _ in range(imageW)]
        for index, rect in enumerate(rects):
            if int(rect[1]) < imageW:
                self.r_index[int(rect[1])].append(index)
            else:
                self.r_index[imageW - 1].append(index)

    def calc_overlap_for_Yaxis(self, index1, index2):
        height1 = self.rects[index1][3] - self.rects[index1][1]
        height2 = self.rects[index2][3] - self.rects[index2][1]
        y0 = max(self.rects[index1][1], self.rects[index2][1])
        y1 = min(self.rects[index1][3], self.rects[index2][3])
        Yaxis_overlap = max(0, y1 - y0) / max(height1, height2)

        return Yaxis_overlap

    def calc_overlap_for_Xaxis(self, index1, index2):
        width1 = self.rects[index1][2] - self.rects[index1][0]
        width2 = self.rects[index2][2] - self.rects[index2][0]
        x0 = max(self.rects[index1][0], self.rects[index2][0])
        x1 = min(self.rects[index1][2], self.rects[index2][2])

        Yaxis_overlap = max(0, x1 - x0) / max(width1, width2)
        return Yaxis_overlap

    def get_proposal(self, index):
        rect = self.rects[index]
        for left in range(rect[1] + 1, min(self.imageW - 1, rect[3] + self.max_dist)):
            for idx in self.r_index[left]:
                if self.calc_overlap_for_Xaxis(index, idx) > self.overlap_threshold:

                    return idx

        return -1

    def sub_graphs_connected(self):
        sub_graphs = []
        for index in range(self.graph.shape[0]):
            if not self.graph[:, index].any() and self.graph[index, :].any():
                v = index
                sub_graphs.append([v])
                while self.graph[v, :].any():

                    v = np.where(self.graph[v, :])[0][0]
                    sub_graphs[-1].append(v)
        return sub_graphs
    
    def connect_boxes(self):
        for idx, _ in enumerate(self.rects):

            proposal = self.get_proposal(idx)
            if proposal >= 0:

                self.graph[idx][proposal] = 1

        sub_graphs = self.sub_graphs_connected() 
        return sub_graphs
