# LEND: Towards Automatic Network Diagram Comprehension

LEND is the abbreviation for Layered Extraction of Network Diagrams, a tool for automatic diagram comprehension.
## Feature
LEND can translate network diagrams to model-comprehensible texts. It includes:
(1) designing and using an abstraction called NDJ to save three visual elements in network diagrams in the form of three entities;

(2) more general icon detection strategy with careful classification;

(3) domain knowledge injection when performing text attribution;

(4) prompt engineering for better end-to-end performance;

## Performance
LEND shows outstanding performance in icon detection, topology detection, text attribution and end-to-end usefulness.
## Requirement
### Software Requirements

You should install the Python  libraries as instructed by `src/README.md` and `src/requirements.txt`and Python 3.



### Hardware Requirement

You should have  an NVIDIA(R) GPU with at least 24GB memory as we need to load in ViT-L and other models. Our experiment is conducted on NVIDIA(R) RTX A6000 GPU.



### License

LEND is currently released under AGPL-3.0 License. This [OSI-approved](https://opensource.org/licenses/) open-source license is ideal for students and enthusiasts, promoting open collaboration and knowledge sharing. See the [LICENSE](https://www.gnu.org/licenses/agpl-3.0.en.html) file for more details.