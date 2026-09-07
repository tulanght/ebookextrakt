# SPEC: Dọn dẹp & Phân loại D:\Extracted-EBOOKS

**Mục đích:** Trước khi build search app, cần data sạch và có cấu trúc.  
**Thực hiện bởi:** Antigravity  
**Không cần hỏi lại:** Danh sách phân loại đã chốt bên dưới.

---

## Task 1: Re-extract 7 cuốn lỗi

### Danh sách cần fix

| Folder | Vấn đề | Hành động |
|--------|---------|-----------|
| `Battle Elephants and Flaming Foxes` | 0 chapters, 0 words | Re-extract, kiểm tra file gốc còn không |
| `Influence of Echeveria gibbiflora DC...` | 0 chapters, 0 words | Re-extract |
| `Making Bird Friendly Birdhouses` | 0 chapters, 0 words | Re-extract |
| `The guests of ants how myrmecophiles...` | 0 chapters, 0 words | Re-extract |
| `The Insect Crisis The Fall of...` | 0 chapters, 0 words | Re-extract |
| `The Little Book of Planting Trees (Max Adams)` | 0 chapters, 0 words | Re-extract |
| `Physiological Systems in Insects (Marc J. Klowden...)` | **1 chapter nhưng 311,738 từ** = parser gộp tất cả vào 1 chapter | Re-extract với chapter splitter khác — đây là cuốn KH lớn, rất valuable |

### Quy trình
1. Tìm file gốc (PDF/EPUB) trong `D:\Ebooks\` hoặc nơi lưu trữ gốc
2. Nếu file gốc tồn tại → re-run extraction pipeline
3. Nếu không tìm thấy file gốc → ghi chú vào `audit_results.json` field `"missing_source": true`
4. Sau re-extract → cập nhật `audit_results.json` với kết quả mới

---

## Task 2: Phân loại 416 cuốn

### Cấu trúc mục tiêu

Tạo file `D:\Extracted-EBOOKS\_classification.json` với schema:

```json
{
  "version": "1.0",
  "total": 416,
  "classified_at": "2026-04-17",
  "books": [
    {
      "folder": "tên thư mục",
      "category": "animal|plant|overlap|off",
      "site": "kenhdongvat|caymongnuoc|both|none",
      "notes": "ghi chú nếu cần"
    }
  ]
}
```

**Không di chuyển thư mục vật lý** — chỉ tạo metadata file để tránh break catalog paths.

---

## Danh sách phân loại đầy đủ (đã chốt — KHÔNG cần tự suy luận)

### ANIMAL — site: kenhdongvat (286 cuốn)

```
(Ethology and Behavioral Ecology of Marine Mammals) Randall W. Davis, Anthony M
100 Birds, Butterflies, and Other Insects Step by Step Realistic Line Drawing
30 Second Zoology
A Curious Collection of Dangerous Creatures
A Curious Collection of Peculiar Creatures
A Curious Collection of Wild Companions
A Field Guide to Harlequins and Other Common Ladybirds of Britain and Ireland
A Field Guide to the Birds of Peninsular Malaysia and Singapore
A Field Guide to the Reptiles of Thailand
A Guide to the Deer of the World
A Handbook to the Swallows and Martins of the World
A History of the World in 100 Animals
A Most Remarkable Creature
A Natural History of Bat Foraging
A Natural History of Insects in 100 Limericks
A Natural History of Shells
A Pocket Guide to Sharks of the World
A World in a Shell
Alien Worlds
All About Birds California
All about Birds Midwest
All about Birds Northeast
All about Birds Northwest
All about Birds Southeast
All About Birds Southwest
All About Birds Texas and Oklahoma
Alligators The Illustrated Guide to Their Biology, Behavior, and Conservation
Amazonian Mammals (Wilson R. Spironello, Adrian A. Barnett etc
AMNH Birds of North America Eastern
AMNH Birds of North America Western
Among the Bone Eaters Encounters with Hyenas in Harar
Animal Antics
Animal Atlas
Animal Knowledge Genius!
Animal Teams
Animal The Definitive Visual Guide
Animals Up Close
Ants
Australia's Dangerous Snakes
Avian Illuminations A Cultural History of Birds
Backyard Bees
Bark Beetles Biology and Ecology of Native and Invasive Species (Fernando E. Vega, Richard W
Bats
Battle Elephants and Flaming Foxes
Beepedia
Bees of the World
Beetles of the World
Beetles of Western North America
Beginning of the Age of Mammals
Being Salmon, Being Human
Big Cats in the Wild
Biology of Turtles (Jeanette Wyneken, Matthew H
Bird
Bird Migration
Bird Senses
Birding to Change the World
Birds and Us
Birds in the Ancient World
Birds in Winter
Birds of Arizona Field Guide
Birds of Belize
Birds of Central America
Birds of Costa Rica
Birds of Mongolia
Birds of North America
Birds of Prey of the East
Birds of Prey of the West
Birds of Puerto Rico and the Virgin Islands
Birds of the Middle East
Birds of the Pacific Northwest
Birds of the West Indies Second Edition
Birds of the World
Born to be Wild
Bovids of the World
Britain's Birds
Butterflies
Buzz, Sting, Bite
Canids of the World
Carnivoran Ecology
Celebrating Birds
Cheetah
Chinese Wildlife
Clever Creatures
Common Bees of Eastern North America
Concise Pond Wildlife Guide
Crabs
Cuckoos of the World (Johannes Erritzøe, Frederik Brammer etc
Did You Know Animals
Display Appearance, posture and behaviour in the animal kingdom
Diving Beetles
Dynasties
Elephant
Elephants
Elephants and Their Fossil Relatives A 60 Million Year Journey (Asier Larramendi, Marco P. Ferretti) (z library.sk, 1lib.sk, z lib
Empire of Ants
Encyclopedia of Insects
Encyclopedia of Insects, Second Edition
Europe's Birds
Europe's Dragonflies
Everything You Need to Know About Snakes
Extraordinary Insects
Far from Land
Felids and Hyenas of the World
Field Guide to Carnivores of the World, 2nd Edition
Field Guide to the Birds of Bangladesh
Field Guide to the Birds of Ghana
Field Guide to the Wildlife of New Zealand
Fish and Amphibians Britannica Illustrated Science Library
Flying Dinosaurs How Fearsome Reptiles Became Birds
Following the Wild Bees
Frogs of the World
Galpagos
Garden Insects of North America
Giant Sloths and Sabertooth Cats
Great Adaptations Star Nosed Moles, Electric Eels, and Other Tales of Evolution's Mysteries Solved
Handbook of Mammals of Madagascar
Handbook of Whales, Dolphins and Porpoises
Healthy Bee, Sick Bee
Hidden Dangers
Honey Bee Biology
How Birds Evolve
How Birds Live Together
How Snakes Work Structure, Function and Behavior of the World's Snakes
How to Know the Birds
How to Speak Whale
Identifying Birds by Colour
Insects and Their Beneficial Microbes
Inshore Fishes of Britain and Ireland (Lin Baldock Frances Dipper)
Invertebrates Fourth Edition (Richard C
Islands and Snakes
Kaleidoscope of Creatures
Kingfishers, Bee eaters and Rollers
Knowledge Encyclopedia Ocean!
Koala
Koala A Life in Trees
Learn to Paint Wildlife Quickly
Life Between the Tides
Life Sculpted
Lizards of the World
Loons
Mammalian Paleoecology
Mammalian Sexuality
Mammals
Mammals of South east Asia
Marine Mammals, Third Edition Evolutionary Biology (Annalisa Berta, James L. Sumich, Kit M
Mass Production of Beneficial Organisms
Migration
Mosquitoes of the World
Naturalized Parrots of the World
Nature Guide Snakes and Other Reptiles and Amphibians
Nature Underfoot Living with Beetles, Crabgrass, Fruit Flies, and Other Tiny Life Around Us
New World Monkeys
Norman I. Platnick Spiders of the world _ a natural history (2020) libgen
Ocean Bestiary
Opossums
Owls
Owls of the World (Claus Konig, Freidhelm Weick etc
Photographic Guide to Snakes, Other Reptiles and Amphibians of East Africa
Photography Birds
Physiological Systems in Insects (Marc J. Klowden (Auth
Plankton Wonders of the Drifting World
Platypus Matters
Pocket Photo Guide to the Mammals of North Africa and the Middle East
Poison Frogs Feb 2017
Raptors of Mexico and Central America
Reproductive Strategies in Insects; 1
Reptiles and Amphibians of Australia
Reptiles and Dinosaurs Britannica Illustrated Science Library
Return to the Sea The Life and Evolutionary Times of Marine Mammals
Robins and Chats
RSPB Spotlight Crows
Salamanders (Ashley W. Seifert, Joshua D
Salmon A Fish, the Earth, and the History of a Common Fate
Sarah Brown The Cat_ A Natural and Cultural History Princeton University Press (2020)
Sea Mammals
Seahorses
Secrets of Snakes
Secrets of the Octopus
Semi aquatic Mammals Ecology and Biology
Sharkpedia
Sharks of the World
Shells
Shells of the World
Shrikes and Bush shrikes
Shrikes of the World
Small Wild Cats (James Sanderson, Patrick Watson) (z lib
Snakes of Central and Western Africa (Chippaux, Jean PhilippeJackson, Kate) (z lib
Snakes of the World
Snakes of the World A Catalogue of Living and Extinct Species (Van Wallach, Kenneth L. Williams, Jeff Boundy) (z lib
Snow Leopards. Biodiversity of the World Conservation from Genes to Landscapes (Tom McCarthy, David Mallon, Philip J
Southern African Wildlife
Super Fly
Tadpole Hunter
Tasmanian Devil
Tasmanian Tiger
Tears for Crocodilia
Ten Birds That Changed the World
The Animal Atlas
The Arctic Guide Wildlife of the Far North (Sharon Chester)
The Backyard Birding Bible [5 in 1] How to Attract, Record, Identify and Photograph Birds in Your Garden Including DIY Bird Houses, Feeders, and Baths
The Bee
The Behavioural Biology of Zoo Animals
THE BIG CATS
The Biology and Conservation of Wild Felids
The Bird Atlas
The Bird Name Book
The Bird Way
The Bird Way A New Look at How Birds Talk, Work, Play, Parent, and Think
The Birds of East Africa Kenya, Tanzania, Uganda, Rwanda, Burundi
The Book of Beetles A Life Size Guide to Six Hundred of Natures Gems (Patrice Bouchard)
The Book of Brilliant Bugs
The Book of Caterpillars A Life Size Guide to Six Hundred Species From Around the World
The Book of Frogs
The Book of Snakes
The Chicken
The Complete Insect Anatomy, Physiology, Evolution, and Ecology (David A
The Cow
The Creative Lives of Animals
The Extraordinary World of Birds
The Fish in the Forest
The Goat
The Great Eagles Their Evolution, Ecology and Conservation
The Hunting Apes
The Hyena Scientist
The Insect Crisis The Fall of the Tiny Empires that Run the World (Oliver Milman)
The insects Structure and function (R. F
The Invertebrate Tree of Life
The Kingdon Pocket Guide to African Mammals
The Last Butterflies
The Last of Its Kind
The Lion
The Little Book of Beetles
The Little Book of Butterflies
The Lives of Bees
The Lives of Beetles
The Lives of Octopuses and Their Relatives
The Lives of Sharks
The Magnificent Book of Creatures of the Abyss
The Mind of a Bee
The Modern Bestiary
The Most Perfect Thing
The Natural History of Primates a Systematic Survey of Ecology and Behavior
The New York Wildlife Encyclopedia
The Owl
The Pig
The Polyandrous Queen Honey Bee Biology and Apiculture
The Princeton Field Guide to Mesozoic Sea Reptiles
The Princeton Field Guide to Prehistoric Mammals (Donald R
The Rise and Reign of the Mammals
The Rise of Reptiles
The Salmon
The Science of Animals
The Secret Life of Foxes
The Secret Life of the Adder
The Secret Perfume of Birds
The Secret Social Lives of Reptiles
The Solitary Bees Biology, Evolution, Conservation
The Surprising Lives of Bark Beetles
The Trials of Life
The Who, What, Why of Zoology
The Wild Cat Book Everything You Ever Wanted to Know About Cats
The Wildlife of Southern Africa
The World's Most Ridiculous Animals
Threatened and Recently Extinct Vertebrates of the World (Matthew Richardson)
Thylacine
Tigers of the World. The Science, Politics, and Conservation of Panthera tigris (Ronald Tilson and Philip J. Nyhus (Eds.)) (z lib
Tooth and Claw
Turtles of the World
Velvet Ants of North America
Venomous Snakes of the World
Walker's Mammals of the World
Wasps of the World
Whale The Illustrated Biography (Asha de Vos) (z library.sk, 1lib.sk, z lib
What an Owl Knows The New Science of the Worlds Most Enigmatic Birds (Jennifer Ackerman)
What Insects Do, and Why
What Is a Bird
What It's Like to Be a Bird
What's the Difference Animals
What's Where on Earth Animal Atlas
Wild Cats of the World
Wild Honey Bees
Wild Life!
Wild Waters A wildlife and water lover's companion to the aquatic world
Wildcats
Wildlife of Britain and Ireland
Wildlife of Ecuador A Photographic Field Guide to Birds, Mammals, Reptiles, and Amphibians
Wildlife of the World
Wildlife Photography Fieldcraft
Zoology
Zoology Understanding the Animal World
```

**Ghi chú duplicate:** `Walker's Mammals of the World` xuất hiện 2 lần trong danh sách — kiểm tra xem có phải 2 edition khác nhau không. Nếu trùng nội dung → giữ 1, xóa cái còn lại.

---

### PLANT — site: caymongnuoc (71 cuốn)

```
100 Plants that Heal
1001 Magical Plants
A Beginner's Guide to Succulent Gardening
A Plant for Every Day of the Year
Aloes in Southern Africa
Aloes The genus Aloe
Anthracnose pathogen of the succulent plant Echeveria 'Perle von Nürnberg'
Botanical Icons
Botany for Gardeners
Cacti and Succulents
Cacti and Succulents for Cold Climates 274 Outs
Cacti of Texas, Neighboring States (Weniger D
Cactus and Succulent Plants
Cactus and Succulents (Linda Brandt)
Chromosomal numbers in parental and hybrid plants of the genus iEcheveriai (Cepeda Cornejo, V. RamÃ_rez Maceda etc
Container Succulents
Designing with Succulents
DIY Succulents From Placecards to Wreaths, 35+ Ideas for Creative Projects with Succulents
Encyclopedia of Plants and Flowers
Ferocactus
Finding the Mother Tree
First Report of Leaf Spot on Echeveria spp
Flora
Florapedia
Guide to Succulents of Southern Africa
Handbook of Photosynthesis; Fourth Edition
How Plants Work
Idiot's Guides Succulents
In the Name of Plants
Influence of Echeveria gibbiflora DC aqueous crude extract on mouse sperm energy metabolism and calcium dependent channels
John Bagnasco, Bob Reidmuller Success with Succulents_ Choosing, Growing, and Caring for Cactuses and Other Succulents Cool Springs Press
Kalanchoe (Crassulaceae) in Southern Africa Classification, Biology, and Cultivation
Kew Gardener's Guide to Growing Cacti and Succulents
Kingdom of Plants A Journey Through Their Evolution
Plant Families A Guide for Gardeners and Botanists
RHS Practical Cactus and Succulent Book
RHS the Tree in My Garden
Seaweeds of the World
Star Cactus (Astrophytum asterias)
Stylish Succulents
Succulent Paradise – Twelve great gardens of the world
Succulents
Succulents and All things Under Glass
Succulents Simplified Growing, Designing, and Crafting with 100 Easy Care Varieties
THE ESSENTIAL GUIDE TO SUCCULENT GARDENING A Beginner's Guide to Growing Succulent Plants Indoors and Outdoors
The book of cacti and other succulents (Claude Chidamian)
The Cactus Hunters
The Gardener's Botanical
The Gardener's Guide to Succulents
The Heartbeat of Trees
The Hidden Company That Trees Keep
The Kew Gardener's Guide to Growing Bulbs
The Little Book of Cacti and Other Succulents
The Little Book of Planting Trees (Max Adams)
The Little Book of Trees
The Plant Lover's Guide to Sedums
The Timber Press Guide to Succulent Plants of the World A Comprehensive Reference to More than 2000 Species
The Tree Book
The Treeline
The World Atlas of Trees and Forests
Treepedia
Trees of Life
Trees, Leaves, Flowers & Seeds
Twelve Trees
Wild Your Garden
```

---

### OVERLAP — site: both (19 cuốn)

*Liên quan đến cả động vật lẫn thực vật / môi trường chung*

```
A Natural History of the Future
Abundance Estimation
Asia's Greatest Wildlife Sanctuaries
Chris Packham's Nature Handbook
Coral Reefs
Creating Wild life Friendly Gardens Bendigo (Green Gecko Publications)
Earth's Incredible Oceans
How Life Works
How to Attract Birds to Your Garden
Invasive Animals and Plants in Massachusetts Lakes and Rivers; Lessons for International Aquatic Management
Life from Above
Natural History
Natural Habitats and Wildlife Gardening Inviting Nature Into Your Backyard (Shaun McCoshum) (z library.sk, 1lib.sk, z lib
Native Plant Gardening for Birds, Bees & Butterflies
Ocean
Paths of Pollen
Pollinators & Pollination
RHS Companion to Wildlife Gardening
Sex in City Plants, Animals, Fungi, and More
Spring
Still Water
Tapestries of Life
The Arctic Guide
The Biology Book
The Deep Ocean
The Living Planet The State of the Worlds Wildlife (Norman Maclean)
The Ocean Speaks
The Rainforest Book
The Science of the Ocean
The Sounds of Life How Digital Technology Is Bringing Us Closer to the Worlds of Animals and Plants (Karen Bakker)
The Voices of Nature
The Wonders of Nature
```

---

### OFF-TOPIC — site: none (20 cuốn)

*Không liên quan, không có giá trị cho pipeline hiện tại*

```
0198502133
119501
119521
Ashis K
Atlas Obscura
Chapter 1
CoverImage
DKSupernatural Creatures • Mythical and Sacred Creatures from Around the World (DK) (z library.sk, 1lib.sk, z lib
DK Children's Encyclopedia
Doctors by Nature
Dumpling and His Wife (Steven A
Hello Tiny World
Japan
Kelly B
Steve N. G
The Big Book of Monsters Volume One An Illustrated Encyclopedia of Myths, Folktales and Legendary Creatures (Chad ODell Roberts)
The Earth Transformed
The Five Million Year Odyssey
The Lotus Sūtra
The Official U.S
```

---

## Task 3: Cập nhật audit_results.json

Sau khi có `_classification.json`, cập nhật `audit_results.json` để thêm field `category` vào mỗi entry trong `all_folders`. Format:

```json
"by_category": {
  "animal": 286,
  "plant": 71,
  "overlap": 32,
  "off": 20,
  "low_quality": 7
}
```

---

## Acceptance Criteria

- [ ] `D:\Extracted-EBOOKS\_classification.json` tồn tại với đủ 416 entries
- [ ] `audit_results.json` có `by_category` đã populate
- [ ] 7 cuốn low-quality đã thử re-extract (ghi kết quả vào audit)
- [ ] `Physiological Systems in Insects` đã re-extract ra nhiều chapters (không còn 1 chapter)
- [ ] Duplicate `Walker's Mammals of the World` đã kiểm tra và xử lý
- [ ] Không di chuyển thư mục vật lý trong `D:\Extracted-EBOOKS\`

---

## Không cần làm (scope của spec này)

- KHÔNG build search/FTS5 index (task tiếp theo, sau khi data sạch)
- KHÔNG dịch hay tạo bài viết
- KHÔNG thay đổi catalog paths trong E-Extract app
