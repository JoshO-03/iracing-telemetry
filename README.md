# iracing-ibt-parser

This is a very basic example project that parses iRacing IBT files to extract useful telemetry data.

## Description

The `iracing-ibt-parser` is a tool designed to help iRacing enthusiasts and developers extract and analyze telemetry data from IBT files. This can be useful for performance analysis, strategy planning, and improving driving skills.

## Installation

To install the `iracing-ibt-parser`, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/matthias-hampel/iracing-ibt-parser.git
   ```
2. Navigate to the project directory:
   ```sh
   cd iracing-ibt-parser
   ```
3. Install the required dependencies:
   ```sh
   npm install
   ```

## Usage

To use the `iracing-ibt-parser`, follow these steps:

1. If you want to analyse your own telemetry file, replace it with the `telemetry.ibt` in the project folder.
2. **Attention:** Larger telemetry files will produce a lot (and I mean A LOT) output. You might want to adjust the `sample` variable in the `index.ts` file. This variable defines where to start with the output.
3. Run:
   ```sh
   npm run dev
   ```
4. Watch the output :)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

