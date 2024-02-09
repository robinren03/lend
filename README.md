# LEND: Towards Automatic Network Diagram Comprehension

Welcome to LEND (the Layered Extraction of Network Diagrams)  a tool enabling automatic diagram comprehension.
## Feature
LEND can translate network diagrams to model-comprehensible texts. It includes:
(1) designing and using an abstraction called NDJ to save three visual elements in network diagrams in the form of three entities;

(2) more general icon detection strategy with careful classification;

(3) domain knowledge injection when performing text attribution;

(4) prompt engineering for better end-to-end performance.

LEND currently supports to MiniNet and to LLM output generation.

## Performance
LEND shows outstanding performance in icon detection, topology detection, text attribution and end-to-end usefulness.

### Icon detection

For the overall performance of LEND to other models,

![icon-all](.\figs\icon-all.png)

For each class, each model performs:

![iconp](.\figs\iconp.png)

![iconr](.\figs\iconr.png)

### Topology detection and text attribution

| Model    | MP   | MR   | DP   | DR   | GED  | WP   | WR   |
| -------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| GPT-4V   | 38%  | 26%  | 78%  | 55%  | 6.3  | 11%  | 9%   |
| LEND     | 99%  | 66%  | 97%  | 76%  | 3.9  | 61%  | 56%  |
| $\Delta$ | +61% | +40% | +19% | +21% | -2.4 | +50% | +47% |

*Table: Evaluation on topology and JSON generation*

MP - Precision of Adjacency Matrix, MR - Recall of Adjacency Matrix;

DP - Precision of Degree Vector, DR - Recall of Degree Vector;

GED - Graph Edit Distance (Timeout - 5s on Intel(R) Xeon(R) Gold 5218R CPU @ 2.10GHz)

WP - Precision of Text Attribution by Word, WR - Recall of Text Attribution by Word

### End-to-end usefulness

Score compared to other models.

![scores](.\figs\accuracy.png)

ablation study on task-specific interpreter
| LEND(GPT-4V)    | full |  -dis ambiguity  | -prompt engineering  |
| -------- | ---- | ---- | ---- |
| score  | 48.28 | 40.26  | 42.07 |


## Requirement
### Software Requirements

You should install the Python  libraries as instructed by `src/README.md` and `src/requirements.txt`and Python 3.



### Hardware Requirement

You should have  an NVIDIA(R) GPU with at least 24GB memory as LEND requires to load in ViT-L and other models. Our experiment was conducted on NVIDIA(R) RTX A6000 GPU.



### License

LEND is currently released under AGPL-3.0 License. This [OSI-approved](https://opensource.org/licenses/) open-source license is ideal for students and enthusiasts, promoting open collaboration and knowledge sharing. See the [LICENSE](https://www.gnu.org/licenses/agpl-3.0.en.html) file for more details.