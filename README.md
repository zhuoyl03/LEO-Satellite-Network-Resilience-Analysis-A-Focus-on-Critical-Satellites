# Hypatia

## Author's Research Extension

This fork contains the author's independent research extension under
[`project/`](project/). This extension is not part of the original Hypatia IMC
2020 paper. The original Hypatia framework and its citation are kept below for
attribution.

The added project analyzes LEO satellite network resilience by:

* building time-varying satellite/ground-station graph snapshots;
* deleting high-impact satellites and recomputing reachable paths;
* measuring RTT, path changes, and connectivity degradation after deletion;
* providing a cleaned project entry point and configuration layer.

This extension supports the following paper:

> Zhuoyuan Li, Wenyi Morty Zhang, Wenhao Chen, Yiyan Hu, and Weyl Lu.
> **LEO Satellite Network Resilience Analysis: A Focus on Critical Satellites.**
> In *Proceedings of the 2nd International Workshop on LEO Networking and
> Communication (LEO-NET '24)*, pages 13-18, 2024.
> DOI: [10.1145/3697253.3697267](https://doi.org/10.1145/3697253.3697267)
> / [ACM PDF](https://dl.acm.org/doi/pdf/10.1145/3697253.3697267)

If you use this project extension, please cite:

```bibtex
@inproceedings{li2024leo_resilience,
  author = {Li, Zhuoyuan and Zhang, Wenyi Morty and Chen, Wenhao and Hu, Yiyan and Lu, Weyl},
  title = {{LEO Satellite Network Resilience Analysis: A Focus on Critical Satellites}},
  booktitle = {{Proceedings of the 2nd International Workshop on LEO Networking and Communication}},
  series = {{LEO-NET '24}},
  pages = {13--18},
  year = {2024},
  doi = {10.1145/3697253.3697267}
}
```

Start here if you are looking for the author's added work:

* project code and instructions: [`project/README.md`](project/README.md)
* main entry point: [`project/satellites_analysis.py`](project/satellites_analysis.py)
* risk displacement first-step CLI: [`run_risk_displacement_first_step.py`](run_risk_displacement_first_step.py)
* centralized paths/configuration: [`project/config.py`](project/config.py)

Quick smoke test:

```bash
conda run -n hypatia python project/satellites_analysis.py --smoke --deletion_counts 50
```

Generated graph/path/RTT data and figures are intentionally not committed to git
because they are large. See [`project/README.md`](project/README.md) for the
expected output layout and data policy.

## Original Hypatia Framework

Hypatia is a low earth orbit (LEO) satellite network simulation framework. It pre-calculates network state over time, enables packet-level simulations using ns-3 and provides visualizations to aid understanding.

<a href="#"><img alt="Kuiper side-view" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/Kuiper_side_view.png" width="20%" /></a>
<a href="#"><img alt="Telesat top-view" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/Telesat_top_view.png" width="20%" /></a>
<a href="#"><img alt="starlink_paris_luanda_short" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/starlink_paris_luanda_short.png" width="10%" /></a>

It consists of four main components:

* `satgenpy` : Python framework to generate LEO satellite networks and generate 
  routing over time over a period of time. It additionally includes several 
  analysis tools to study individual cases. It makes use of several Python modules
  among which: numpy, astropy, ephem, networkx, sgp4, geopy, matplotlib, 
  statsmodels, cartopy (and its dependent (data) packages: libproj-dev, proj-data,
  proj-bin, libgeos-dev), and exputil.
  More information can be found in `satgenpy/README.md`.
  (license: MIT)

* `ns3-sat-sim` : ns-3 based framework which takes as input the state generated 
  by `satgenpy` to perform packet-level simulations over LEO satellite networks.
  It makes use of the [`satellite`](https://gitlab.inesctec.pt/pmms/ns3-satellite)
  ns-3 module by Pedro Silva to calculate satellite locations over time.
  It uses the [`basic-sim`](https://github.com/snkas/basic-sim/tree/3b32597c183e1039be7f0bede17d36d354696776) 
  ns-3 module to make e.g., running end-to-end TCP flows easier, which makes use of several Python
  modules (e.g., numpy, statsmodels, exputil) as well as several other packages (e.g., OpenMPI, lcov, gnuplot).
  More information can be found in `ns3-sat-sim/README.md`.
  (license: GNU GPL version 2)
  
* `satviz` : Cesium visualization pipeline to generate interactive satellite network
  visualizations. It makes use of the online Cesium API by generating CesiumJS code.
  The API calls require its user to obtain a Cesium access token (via [https://cesium.com/]()).
  More information can be found in `satviz/README.md`.
  (license: MIT)

* `paper` : Experimental and plotting code to reproduce the experiments and 
  figures which are presented in the paper.
  It makes use of several Python modules among which: satgenpy, numpy, networkload, and exputil.
  It uses the gnuplot package for most of its plotting.
  More information can be found in `paper/README.md`.
  (license: MIT)
  
(there is a fifth folder called `integration_tests` which is used for integration testing purposes)

The original Hypatia code repository was introduced and used in "Exploring the “Internet from space” with Hypatia" 
by Simon Kassing*, Debopam Bhattacherjee*, André Baptista Águas, Jens Eirik Saethre and Ankit Singla
(*equal contribution), which is published in the Internet Measurement Conference (IMC) 2020.

BibTeX citation:
```
@inproceedings {hypatia,
    author = {Kassing, Simon and Bhattacherjee, Debopam and Águas, André Baptista and Saethre, Jens Eirik and Singla, Ankit},
    title = {{Exploring the “Internet from space” with Hypatia}},
    booktitle = {{ACM IMC}},
    year = {2020}
}
```

## Getting started

1. System setup:
   - Python version 3.7+
   - Recent Linux operating system (e.g., Ubuntu 18+)

2. Install dependencies:
   ```
   bash hypatia_install_dependencies.sh
   ```
   
3. Build all four modules (as far as possible):
   ```
   bash hypatia_build.sh
   ```
   
4. Run tests:
   ```
   bash hypatia_run_tests.sh
   ```

5. The reproduction of the paper is essentially the tutorial for Hypatia.
   Please navigate to `paper/README.md`.

### Visualizations
Most of the visualizations in the paper are available [here](https://leosatsim.github.io/).
All of the visualizations can be regenerated using scripts available in `satviz` as discussed above.

Below are some examples of visualizations:

- SpaceX Starlink 5-shell side-view (left) and top-view (right). To know the configuration of the shells, click [here](https://leosatsim.github.io/).

  <a href="#"><img alt="Starlink side-view" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/Starlink_side_view.png" width="45%" /></a>
  <a href="#"><img alt="Starlink top-view" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/Starlink_top_view.png" width="45%" /></a>

- Amazon Kuiper 3-shell side-view (left) and top-view (right). To know the configuration of the shells, click [here](https://leosatsim.github.io/kuiper.html).

  <a href="#"><img alt="Kuiper side-view" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/Kuiper_side_view.png" width="45%" /></a>
  <a href="#"><img alt="Kuiper top-view" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/Kuiper_top_view.png" width="45%" /></a>

- RTT changes over time between Paris and Luanda over Starlink 1st shell. Left: 117 ms, Right: 85 ms. Click on the images for 3D interactive visualizations.

  <a href="https://leosatsim.github.io/starlink_550_path_Paris_1608_Luanda_1650_46800.html"><img alt="starlink_paris_luanda_long" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/starlink_paris_luanda_long.png" width="35%" /></a>
  <a href="https://leosatsim.github.io/starlink_550_path_Paris_1608_Luanda_1650_139900.html"><img alt="starlink_paris_luanda_short" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/starlink_paris_luanda_short.png" width="35%" /></a>

- Link utilizations change over time, even with the input traffic being static. For Kuiper 1st shell, path between Chicago and Zhengzhou at 10s (top) and 150s (bottom). Click on the images for 3D interactive visualizations.

  <a href="https://leosatsim.github.io/kuiper_630_path_wise_util_Chicago_1193_Zhengzhou_1243_10000.html"><img alt="kuiper_Chicago_Zhengzhou_10s" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/kuiper_Chicago_Zhengzhou_10s.png" width="90%" /></a>
  <a href="https://leosatsim.github.io/kuiper_630_path_wise_util_Chicago_1193_Zhengzhou_1243_150000.html"><img alt="kuiper_Chicago_Zhengzhou_150s" src="https://raw.githubusercontent.com/leosatsim/leosatsim.github.io/master/images/kuiper_Chicago_Zhengzhou_150s.png" width="90%" /></a>
