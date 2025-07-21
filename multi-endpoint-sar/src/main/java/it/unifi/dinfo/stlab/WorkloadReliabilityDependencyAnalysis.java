package it.unifi.dinfo.stlab;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

public class WorkloadReliabilityDependencyAnalysis {

    private static final String RESULT_COLS = "Arrival Rate,Aging Rate,Unreliability";

    public static void main(String[] args) throws IOException {

        Path experimentPath = createExperimentPath();
        String resultFilePath = initializeResultFile(experimentPath);

        double serviceRateA = 25. / 10.;

        ReplicaSetBuilder builder = new ReplicaSetBuilder();
        builder.setRepairRate(10);
        builder.setRejuvenationRate(10);
        builder.setFalsePositiveProb(25. / 100.);
        builder.setFalseNegativeProb(25. / 100.);

        int numOfReplicas = 6;

        builder.setNumOfReplicas(numOfReplicas);

        List<Double> agingRates = List.of(0.01, 0.1, 0.3, 0.5, 0.8);
        List<Double> arrivalRates = List.of(1., 5., 10., 15., 20., 25., 30., 50., 100.);

        for (Double workload : arrivalRates) {
            for (Double agingRate : agingRates) {

                Endpoint endpoint = new Endpoint("A", workload, serviceRateA, agingRate,
                        agingRate);

                ReplicaSetModel replicaSetModel = builder.build(endpoint);
                replicaSetModel.analyze();


                Map<Endpoint, BigDecimal> steadyStateEndpointsReliabilities = replicaSetModel
                                .getSteadyStateEndpointsReliabilities();

                BigDecimal reliability = steadyStateEndpointsReliabilities.get(endpoint);

                addRow(resultFilePath, workload + "," + agingRate + "," + reliability );

            }

        }

    }

    private static Path createExperimentPath() throws IOException {
        LocalDateTime now = LocalDateTime.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
        String formattedDate = now.format(formatter);
        String subfolder = "exp-" + formattedDate;
        Path path = Paths.get("experiment-results", subfolder);
        Files.createDirectories(path);
        System.out.println("Experiment Directory: " + path.toAbsolutePath());
        return path;
    }

    private static void saveEndpointInfo(Path basePath, Endpoint... endpoints) {
        String endpointInfoFileName = "endpointInfo.csv";
        File file = new File(basePath.toFile(), endpointInfoFileName);
        String filePath = file.getPath();
        createCsv(filePath, Endpoint.getAttributeOreder());
        for (Endpoint endpoint : endpoints) {
            addRow(filePath, endpoint.toString());
        }
    }

    private static void createCsv(String filePath, String cols) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filePath))) {
            writer.write(cols);
            writer.newLine();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void addRow(String filePath, String row) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filePath, true))) {
            writer.write(row);
            writer.newLine();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static String initializeResultFile(Path basePath) {
        String resultsFileName = "workload_reliability.csv";
        File file = new File(basePath.toFile(), resultsFileName);
        String filePath = file.getPath();
        createCsv(filePath, RESULT_COLS);
        return filePath;
    }

}
