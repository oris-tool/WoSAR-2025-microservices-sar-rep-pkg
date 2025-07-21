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

public class ReplicaSetAnalysis {

        private static final String RESULT_COLS = "Endpoint,Configuration,Pool Size,Reliability,Unavailability,Aging Contribution,Resource Usage";

        public static void main(String[] args) throws IOException {

                Path experimentPath = createExperimentPath();

                int totalNumberOfReplicas = 8;

                double arrivalRateA = 100. / 10.;
                double serviceRateA = 25. / 10.;
                double healthyToAgedTendencyA = 10. / 100.;
                double agedToFailedTendencyA = 1. / 100.;

                double arrivalRateB = 50. / 10.;
                double serviceRateB = 50. / 10.;
                double healthyToAgedTendencyB = 1. / 100.;
                double agedToFailedTendencyB = 10. / 100.;
                
                Endpoint endpointA = new Endpoint("A", arrivalRateA, serviceRateA, healthyToAgedTendencyA, agedToFailedTendencyA);
                Endpoint endpointB = new Endpoint("B", arrivalRateB, serviceRateB, healthyToAgedTendencyB, agedToFailedTendencyB);
                List<Endpoint> endpoints = List.of(endpointA, endpointB);

                saveEndpointInfo(experimentPath, endpointA, endpointB);
                String resultFilePath = initializeResultFile(experimentPath);

                ReplicaSetBuilder builder = new ReplicaSetBuilder();
                builder.setRepairRate(10);
                builder.setRejuvenationRate(10);
                builder.setFalsePositiveProb(25. / 100.);
                builder.setFalseNegativeProb(25. / 100.);

                builder.setNumOfReplicas(totalNumberOfReplicas);
                ReplicaSetModel replicaSetModel = builder.build(endpointA, endpointB);
                replicaSetModel.analyze();

                saveModelResults(resultFilePath, replicaSetModel, totalNumberOfReplicas);

                for (int singleEndpointReplicas = 1; singleEndpointReplicas < totalNumberOfReplicas; singleEndpointReplicas++) {
                        for (Endpoint endpoint : endpoints) {
                                builder.setNumOfReplicas(singleEndpointReplicas);
                                ReplicaSetModel singleEndpointReplicaSetModel = builder.build(endpoint);
                                singleEndpointReplicaSetModel.analyze();
                                saveModelResults(resultFilePath, singleEndpointReplicaSetModel, singleEndpointReplicas);
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

        private static String initializeResultFile(Path basePath) {
                String resultsFileName = "analysisResults.csv";
                File file = new File(basePath.toFile(), resultsFileName);
                String filePath = file.getPath();
                createCsv(filePath, RESULT_COLS);
                return filePath;
        }

        private static void saveModelResults(String filePath, ReplicaSetModel replicaSetModel, int poolSize) {
                List<Endpoint> endpoints = replicaSetModel.getEndpoints();
                String loads = "\"" + String.join("+", endpoints.stream().map(Endpoint::id).toList()) + "\"";
                BigDecimal steadyStateResourceUsage = replicaSetModel.getSteadyStateResourceUsage();
                System.out.println("Resource Usage replica set with Loads " + loads + ":" + steadyStateResourceUsage);
                Map<Endpoint, BigDecimal> steadyStateEndpointsReliabilities = replicaSetModel
                                .getSteadyStateEndpointsReliabilities();
                Map<Endpoint, BigDecimal> steadyStateEndpointsUnavailiabilities = replicaSetModel
                                .getSteadyStateEndpointsUnavailiabilities();

                Map<Endpoint, BigDecimal> steadyStateEndpointsAgingContributions = replicaSetModel
                                .getSteadyStateAgingContributions();

                for (Endpoint endpoint : endpoints) {
                        String endpointId = endpoint.id();
                        BigDecimal reliability = steadyStateEndpointsReliabilities.get(endpoint);
                        BigDecimal unavailability = steadyStateEndpointsUnavailiabilities.get(endpoint);
                        BigDecimal agingContribution = steadyStateEndpointsAgingContributions.get(endpoint);
                        String rowToAdd = endpointId + "," + loads+ "," + poolSize + "," + reliability + "," + unavailability + "," + agingContribution + ","
                                        + steadyStateResourceUsage;
                        System.out.println("Unavailability of endpoint " + endpoint.id() + ": " + unavailability);
                        System.out.println("Reliability of endpoint " + endpoint.id() + ": " + reliability);
                        addRow(filePath, rowToAdd);
                }

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

}
